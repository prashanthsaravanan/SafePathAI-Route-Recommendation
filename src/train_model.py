import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

# Load the dataset
df = pd.read_csv("routes_with_paths.csv")

# Mapping categorical values
congestion_map = {"Low": 0, "Medium": 1, "High": 2}
time_map = {"Morning": 0, "Afternoon": 1, "Evening": 2, "Night": 3}

# Apply mappings
df["congestion_level_num"] = df["congestion_level"].map(congestion_map)
df["time_num"] = df["time_of_day"].map(time_map)

# Define the risk label based on accidents and congestion
# You can tweak this logic as needed
def get_risk(row):
    if row["accidents"] >= 5 or row["congestion_level"] == "High":
        return "High Risk"
    elif row["accidents"] >= 3:
        return "Medium Risk"
    else:
        return "Low Risk"

df["risk_label"] = df.apply(get_risk, axis=1)

# Features and target
X = df[["distance_km", "congestion_level_num", "accidents", "time_num"]]
y = df["risk_label"]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Model training
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluation
y_pred = model.predict(X_test)
print("Classification Report:\n", classification_report(y_test, y_pred))

# Save the trained model
joblib.dump(model, "model.pkl")
print("✅ Model saved as model.pkl")

