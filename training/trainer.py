import numpy as np
import joblib
import os
from loguru import logger
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

class ModelTrainer:
    def __init__(self):
        self.models = {
            "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42),
            "XGBoost": XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42),
            "LightGBM": LGBMClassifier(random_state=42)
        }
        self.results = {}

    def load_data(self):
        """Loads preprocessed data from .npy files."""
        X_train = np.load("data/X_train.npy")
        X_test = np.load("data/X_test.npy")
        y_train = np.load("data/y_train.npy")
        y_test = np.load("data/y_test.npy")
        return X_train, X_test, y_train, y_test

    def train_and_evaluate(self, X_train, X_test, y_train, y_test):
        """Trains multiple models and evaluates their performance."""
        best_f1 = 0
        best_model_name = ""

        for name, model in self.models.items():
            logger.info(f"Training {name}...")
            model.fit(X_train, y_train)
            
            y_pred = model.predict(X_test)
            y_prob = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else y_pred
            
            metrics = {
                "Accuracy": accuracy_score(y_test, y_pred),
                "Precision": precision_score(y_test, y_pred),
                "Recall": recall_score(y_test, y_pred),
                "F1": f1_score(y_test, y_pred),
                "ROC_AUC": roc_auc_score(y_test, y_prob)
            }
            
            self.results[name] = metrics
            logger.info(f"{name} Metrics: {metrics}")
            
            if metrics["F1"] > best_f1:
                best_f1 = metrics["F1"]
                best_model_name = name
                # Generate plots for the current best
                self._generate_plots(y_test, y_pred, y_prob)

        logger.info(f"Best Model Found: {best_model_name} with F1 Score: {best_f1}")
        self._save_best_model(best_model_name)
        return best_model_name


    def _generate_plots(self, y_test, y_pred, y_prob):
        """Generates ROC and Confusion Matrix plots."""
        import matplotlib.pyplot as plt
        from sklearn.metrics import RocCurveDisplay, ConfusionMatrixDisplay
        
        os.makedirs("models/plots", exist_ok=True)
        report_img_dir = "report/images"
        os.makedirs(report_img_dir, exist_ok=True)
        
        # ROC Curve
        fig, ax = plt.subplots()
        RocCurveDisplay.from_predictions(y_test, y_prob, ax=ax)
        plt.title("ROC Curve")
        plt.savefig("models/plots/roc_curve.png")
        plt.savefig(f"{report_img_dir}/roc_curve.png")
        plt.close()
        
        # Confusion Matrix
        fig, ax = plt.subplots()
        ConfusionMatrixDisplay.from_predictions(y_test, y_pred, ax=ax)
        plt.title("Confusion Matrix")
        plt.savefig("models/plots/confusion_matrix.png")
        plt.savefig(f"{report_img_dir}/confusion_matrix.png")
        plt.close()
        logger.info(f"Plots synchronized to {report_img_dir}")

    def _save_best_model(self, name):
        """Saves the best model to the models/ directory."""
        os.makedirs("models", exist_ok=True)
        joblib.dump(self.models[name], "models/best_botnet_model.pkl")
        with open("models/best_model_info.txt", "w") as f:
            f.write(name)
        logger.info(f"Saved {name} as best_botnet_model.pkl")

if __name__ == "__main__":
    trainer = ModelTrainer()
    X_train, X_test, y_train, y_test = trainer.load_data()
    trainer.train_and_evaluate(X_train, X_test, y_train, y_test)
