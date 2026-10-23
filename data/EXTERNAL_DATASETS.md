# External Dataset Research Note

## PhysioNet Wearable Device Dataset

**Source:** https://physionet.org/content/wearable-device-dataset/1.0.1/

**License:** Open Data Commons Attribution License (ODC-BY ) v1.0. Check the dataset's license page and attribution rules before downloading or reusing it.

**Population:** Healthy volunteers aged 18–30. The source reports 36 participants in stress sessions, 30 in aerobic exercise sessions, and 31 in anaerobic exercise sessions. These groups may overlap, so do not assume they represent 97 different people.

**Measurements:** A wearable device recorded blood-volume pulse (from which heart rate can be estimated), movement from a three-axis accelerometer, skin temperature, and electrodermal activity. The study also recorded self-reported stress during stress sessions.

**Sampling rates:**
- Blood-volume pulse: 64 samples per second
- Accelerometer: 32 samples per second
- Skin temperature: 4 samples per second
- Electrodermal activity: 4 samples per second

**How it may help:** It could be useful for a separate comparison of short-term stress or exercise signals.

**Important differences:** This dataset is from healthy volunteers doing lab activities. It is not astronaut data and does not contain AstroGuard's complete daily sleep, fatigue, reaction-time, workload, and crew-day measurements.

**Status:** Research only. The dataset has not been downloaded or included in AstroGuard. Keep it separate unless the team first documents how its measurements would be mapped and summarized, and confirms that reuse follows the license.

## NASA dataset to investigate later

NASA's Flight Crew Physiological Data for Crew State Monitoring describes pilot/copilot data from flight-simulator studies. The source page reports 256 samples per second for each sensor, but says that no license is specified.

Source: https://data.nasa.gov/dataset/flight-crew-physiological-data-for-crew-state-monitoring

Treat this as a lead to investigate. Do not add or redistribute its files until the permitted use is confirmed.
