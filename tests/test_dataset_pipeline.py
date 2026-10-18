import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from data_cleaning import (
    check_duplicates,
    check_impossible,
    check_timestamps,
    clean_data,
)
from data_loader import EXPECTED_COLUMNS, PROCESSED_PATH, load_health_data


class DatasetPipelineTests(unittest.TestCase):

    def test_loader_reads_the_expected_columns_and_rows(self):
        data = load_health_data(PROCESSED_PATH)
        self.assertEqual(list(data.columns), EXPECTED_COLUMNS)
        self.assertEqual(len(data), 3600)

    def test_cleaning_keeps_missing_values_blank_and_logs_them(self):
        raw = pd.read_csv(ROOT / "data/raw/astronaut_health_raw.csv")
        cleaned, log = clean_data(raw)

        self.assertEqual(int(cleaned.isna().sum().sum()), 9)
        self.assertEqual(
            int(log["issue"].eq("missing value").sum()),
            8,
        )

    def test_impossible_heart_rate_is_flagged_and_blanked(self):
        raw = pd.read_csv(ROOT / "data/raw/astronaut_health_raw.csv")

        problems = check_impossible(raw)
        self.assertTrue(
            any(problem[3] == "resting_heart_rate" for problem in problems)
        )

        cleaned, log = clean_data(raw)
        row = cleaned[
            (cleaned["crew_id"] == "Crew-19")
            & (cleaned["mission_day"] == 9)
        ]
        self.assertTrue(pd.isna(row.iloc[0]["resting_heart_rate"]))

        heart_rate_log = log[
            (log["crew_id"] == "Crew-19")
            & (log["mission_day"] == 9)
            & (log["column"] == "resting_heart_rate")
        ]
        self.assertEqual(len(heart_rate_log), 1)

    def test_duplicate_detection_finds_duplicate_crew_days(self):
        raw = pd.read_csv(ROOT / "data/raw/astronaut_health_raw.csv").head(2)
        repeated = pd.concat(
            [raw.iloc[[0]], raw.iloc[[0]].assign(sleep_hours=99)],
            ignore_index=True,
        )

        exact_duplicates, repeated_crew_days = check_duplicates(repeated)
        self.assertEqual(exact_duplicates, 0)
        self.assertEqual(repeated_crew_days, 1)

    def test_timestamp_check_accepts_good_dates_and_rejects_bad_dates(self):
        raw = pd.read_csv(
            ROOT / "data/raw/astronaut_health_raw.csv",
            parse_dates=["timestamp"],
        )
        self.assertEqual(check_timestamps(raw), [])

        small = pd.DataFrame({
            "crew_id": ["Crew-01", "Crew-01"],
            "mission_day": [1, 2],
            "timestamp": pd.to_datetime(["2026-01-01", "2026-01-04"]),
        })
        self.assertTrue(check_timestamps(small))

    def test_splits_have_three_groups_and_assign_each_crew_once(self):
        splits_path = ROOT / "data/evaluation/splits.csv"
        splits = pd.read_csv(splits_path)

        self.assertEqual(list(splits.columns), ["crew_id", "split"])
        self.assertEqual(splits["crew_id"].nunique(), 20)
        self.assertFalse(splits["crew_id"].duplicated().any())
        self.assertEqual(
            set(splits["split"]),
            {"train", "validation", "test"},
        )

    def test_model_input_does_not_contain_answer_labels(self):
        features = pd.read_csv(PROCESSED_PATH)
        forbidden = {
            "anomaly_label",
            "anomaly_reason",
            "risk_category",
            "label_source",
            "event",
            "record_type",
            "description",
        }

        self.assertTrue(forbidden.isdisjoint(features.columns))
        self.assertTrue(
            (ROOT / "data/evaluation/ground_truth/scenario_ground_truth.csv").is_file()
        )
        self.assertFalse(
            (ROOT / "data/scenario_ground_truth.csv").exists()
        )

    def test_generator_recreates_identical_csv_files(self):
        with tempfile.TemporaryDirectory() as temp_folder:
            temp_root = Path(temp_folder)
            (temp_root / "src").mkdir()

            shutil.copy2(
                ROOT / "src/generate_synthetic_data.py",
                temp_root / "src/generate_synthetic_data.py",
            )

            def make_hashes():
                subprocess.run(
                    [sys.executable, "src/generate_synthetic_data.py"],
                    cwd=temp_root,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                csv_files = sorted((temp_root / "data").rglob("*.csv"))
                return {
                    str(path.relative_to(temp_root)):
                    hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in csv_files
                }

            self.assertEqual(make_hashes(), make_hashes())


if __name__ == "__main__":
    unittest.main()
