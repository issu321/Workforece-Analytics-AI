"""
Employee Attrition Prediction Engine.
Trains and evaluates multiple ML models for attrition prediction.
Supports: Logistic Regression, Decision Tree, Random Forest, XGBoost, LightGBM, CatBoost.
"""

import os
import json
import pickle
import warnings
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score, 
                             f1_score, roc_auc_score, confusion_matrix, 
                             classification_report, roc_curve)
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import plotly.graph_objects as go
import plotly.express as px

warnings.filterwarnings('ignore')

# Try importing optional libraries
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

try:
    import catboost as cb
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False


def to_native(obj):
    """Recursively convert NumPy types to native Python types for JSON serialization."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.int32, np.int64, np.int8, np.int16, np.uint8, np.uint16, np.uint32, np.uint64)):
        return int(obj)
    elif isinstance(obj, dict):
        return {k: to_native(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_native(i) for i in obj]
    elif isinstance(obj, tuple):
        return tuple(to_native(i) for i in obj)
    return obj


class AttritionPredictor:
    """Main attrition prediction engine."""

    def __init__(self):
        self.models = {}
        self.results = {}
        self.best_model_name = None
        self.best_model = None
        self.preprocessor = None
        self.label_encoders = {}
        self.target_encoder = None
        self.feature_names = None
        self.is_trained = False
        self.X_train = None
        self.y_train = None
        self.target_col = None

    def _find_target_column(self, df):
        """Find the target column in the dataframe."""
        for alt in ['Attrition', 'attrition', 'Attrition_Flag', 'left', 'Left', 'turnover', 'Turnover']:
            if alt in df.columns:
                return alt
        return None

    def preprocess_data(self, df, target_col=None, training=True):
        """Preprocess dataset for ML training/prediction."""
        df = df.copy()

        # Identify target column
        if target_col is None:
            target_col = self._find_target_column(df)

        if target_col is None and training:
            raise ValueError(f"Target column not found. Available: {list(df.columns)}")

        self.target_col = target_col

        # Separate target
        if training and target_col in df.columns:
            y = df[target_col].copy()
            X = df.drop(columns=[target_col])
        else:
            # For prediction, drop target if it exists
            if target_col and target_col in df.columns:
                X = df.drop(columns=[target_col])
            else:
                X = df.copy()
            y = None

        # Identify column types
        numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = X.select_dtypes(include=['object', 'category']).columns.tolist()

        # Handle missing values
        for col in numeric_cols:
            X[col] = X[col].fillna(X[col].median())
        for col in categorical_cols:
            X[col] = X[col].fillna('Unknown')

        # Remove constant columns
        for col in numeric_cols[:]:
            if X[col].nunique() <= 1:
                X = X.drop(columns=[col])
                numeric_cols.remove(col)

        for col in categorical_cols[:]:
            if X[col].nunique() <= 1:
                X = X.drop(columns=[col])
                categorical_cols.remove(col)

        # Encode categorical variables
        if training:
            self.label_encoders = {}
            for col in categorical_cols:
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
                self.label_encoders[col] = le
        else:
            for col in categorical_cols:
                if col in self.label_encoders:
                    le = self.label_encoders[col]
                    # Handle unseen categories
                    X[col] = X[col].apply(lambda x: le.transform([str(x)])[0] 
                                          if str(x) in le.classes_ else -1)
                else:
                    X[col] = 0

        # Encode target if training
        if training and y is not None:
            if y.dtype == 'object' or y.dtype.name == 'category':
                self.target_encoder = LabelEncoder()
                y = self.target_encoder.fit_transform(y.astype(str))
            else:
                self.target_encoder = None

        self.feature_names = list(X.columns)

        # Scale features
        if training:
            self.scaler = StandardScaler()
            X_scaled = pd.DataFrame(self.scaler.fit_transform(X), columns=X.columns, index=X.index)
        else:
            # Ensure same columns as training
            for col in self.feature_names:
                if col not in X.columns:
                    X[col] = 0
            X = X[self.feature_names]
            X_scaled = pd.DataFrame(self.scaler.transform(X), columns=self.feature_names, index=X.index)

        return X_scaled, y

    def train_models(self, df, target_col=None, test_size=0.2):
        """Train all available models and compare performance."""
        X, y = self.preprocess_data(df, target_col, training=True)

        # Split data
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )

        # Define models
        model_configs = {
            'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced'),
            'Decision Tree': DecisionTreeClassifier(max_depth=10, random_state=42, class_weight='balanced'),
            'Random Forest': RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42, class_weight='balanced', n_jobs=-1),
        }

        if XGBOOST_AVAILABLE:
            model_configs['XGBoost'] = xgb.XGBClassifier(
                n_estimators=100, max_depth=6, learning_rate=0.1, 
                random_state=42, use_label_encoder=False, 
                eval_metric='logloss', n_jobs=-1
            )

        if LIGHTGBM_AVAILABLE:
            model_configs['LightGBM'] = lgb.LGBMClassifier(
                n_estimators=100, max_depth=6, learning_rate=0.1,
                random_state=42, verbose=-1, n_jobs=-1
            )

        if CATBOOST_AVAILABLE:
            model_configs['CatBoost'] = cb.CatBoostClassifier(
                iterations=100, depth=6, learning_rate=0.1,
                random_seed=42, verbose=False
            )

        # Train and evaluate each model
        self.results = {}
        best_score = 0

        for name, model in model_configs.items():
            try:
                # Train
                model.fit(self.X_train, self.y_train)

                # Predict
                y_pred = model.predict(self.X_test)
                y_prob = model.predict_proba(self.X_test)[:, 1] if hasattr(model, 'predict_proba') else None

                # Metrics — convert to native Python types
                acc = float(accuracy_score(self.y_test, y_pred))
                prec = float(precision_score(self.y_test, y_pred, average='weighted', zero_division=0))
                rec = float(recall_score(self.y_test, y_pred, average='weighted', zero_division=0))
                f1 = float(f1_score(self.y_test, y_pred, average='weighted', zero_division=0))
                auc = float(roc_auc_score(self.y_test, y_prob)) if y_prob is not None else None

                # Cross-validation
                cv_scores = cross_val_score(model, self.X_train, self.y_train, cv=5, scoring='f1_weighted')
                cv_mean = float(cv_scores.mean())
                cv_std = float(cv_scores.std())

                # Confusion matrix as native Python list
                cm = confusion_matrix(self.y_test, y_pred)
                cm_list = cm.tolist()

                self.results[name] = {
                    'accuracy': round(acc, 4),
                    'precision': round(prec, 4),
                    'recall': round(rec, 4),
                    'f1_score': round(f1, 4),
                    'roc_auc': round(auc, 4) if auc is not None else None,
                    'cv_mean': round(cv_mean, 4),
                    'cv_std': round(cv_std, 4),
                    'confusion_matrix': cm_list,
                    'model': model
                }

                # Select best model by F1 score
                if f1 > best_score:
                    best_score = f1
                    self.best_model_name = name
                    self.best_model = model

            except Exception as e:
                self.results[name] = {'error': str(e)}

        self.models = {name: r['model'] for name, r in self.results.items() if 'model' in r}
        self.is_trained = True

        return self.results

    def predict(self, df, model_name=None):
        """Make predictions on new data."""
        if not self.is_trained:
            raise ValueError("Models must be trained before prediction.")

        model = self.best_model if model_name is None else self.models.get(model_name)
        if model is None:
            raise ValueError(f"Model {model_name} not found.")

        # Preprocess WITHOUT target column
        X, _ = self.preprocess_data(df, training=False)

        predictions = model.predict(X)
        probabilities = model.predict_proba(X)[:, 1] if hasattr(model, 'predict_proba') else None

        # Decode predictions
        if self.target_encoder:
            pred_labels = self.target_encoder.inverse_transform(predictions)
        else:
            pred_labels = predictions

        results = []
        for i in range(len(df)):
            prob = float(probabilities[i]) if probabilities is not None else 0.5

            # Risk classification
            if prob >= 0.7:
                risk_level = 'High Risk'
                risk_score = round(prob * 100, 1)
            elif prob >= 0.4:
                risk_level = 'Medium Risk'
                risk_score = round(prob * 100, 1)
            else:
                risk_level = 'Low Risk'
                risk_score = round(prob * 100, 1)

            results.append({
                'prediction': int(predictions[i]),
                'predicted_label': str(pred_labels[i]),
                'attrition_probability': round(prob, 4),
                'risk_level': risk_level,
                'risk_score': risk_score,
                'confidence': round(max(prob, 1 - prob), 4)
            })

        return results

    def get_feature_importance(self, model_name=None):
        """Get feature importance from the best model."""
        model = self.best_model if model_name is None else self.models.get(model_name)
        if model is None:
            return {}

        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
        elif hasattr(model, 'coef_'):
            importances = np.abs(model.coef_[0])
        else:
            return {}

        # Convert to native Python types
        return dict(sorted(
            zip(self.feature_names, [float(v) for v in importances]),
            key=lambda x: x[1], reverse=True
        ))

    def get_model_comparison_chart(self):
        """Generate Plotly chart for model comparison."""
        valid_results = {k: v for k, v in self.results.items() if 'error' not in v}

        if not valid_results:
            return None

        models = list(valid_results.keys())
        metrics = ['accuracy', 'precision', 'recall', 'f1_score']

        fig = go.Figure()
        colors = ['#6366f1', '#10b981', '#f59e0b', '#ef4444']

        for i, metric in enumerate(metrics):
            values = [valid_results[m].get(metric, 0) for m in models]
            fig.add_trace(go.Bar(
                name=metric.replace('_', ' ').title(),
                x=models,
                y=values,
                marker_color=colors[i],
                text=[f'{v:.3f}' for v in values],
                textposition='auto'
            ))

        fig.update_layout(
            title='Model Performance Comparison',
            barmode='group',
            template='plotly_dark',
            height=500,
            xaxis_title='Model',
            yaxis_title='Score',
            yaxis=dict(range=[0, 1])
        )

        return fig.to_json()

    def get_feature_importance_chart(self):
        """Generate feature importance chart."""
        importance = self.get_feature_importance()
        if not importance:
            return None

        features = list(importance.keys())[:15]
        values = [importance[f] for f in features]

        fig = go.Figure(go.Bar(
            x=values,
            y=features,
            orientation='h',
            marker_color='#6366f1',
            text=[f'{v:.3f}' for v in values],
            textposition='auto'
        ))

        fig.update_layout(
            title='Top Feature Importance',
            template='plotly_dark',
            height=500,
            xaxis_title='Importance',
            yaxis_title='Feature',
            yaxis=dict(autorange='reversed')
        )

        return fig.to_json()

    def get_roc_curve_chart(self):
        """Generate ROC curve chart."""
        if not self.is_trained:
            return None

        fig = go.Figure()

        for name, model in self.models.items():
            try:
                if hasattr(model, 'predict_proba'):
                    y_prob = model.predict_proba(self.X_test)[:, 1]
                    fpr, tpr, _ = roc_curve(self.y_test, y_prob)
                    auc = roc_auc_score(self.y_test, y_prob)
                    fig.add_trace(go.Scatter(
                        x=fpr.tolist(), y=tpr.tolist(),
                        name=f'{name} (AUC={auc:.3f})',
                        mode='lines'
                    ))
            except:
                continue

        fig.add_trace(go.Scatter(
            x=[0, 1], y=[0, 1],
            name='Random',
            mode='lines',
            line=dict(dash='dash', color='gray')
        ))

        fig.update_layout(
            title='ROC Curves',
            template='plotly_dark',
            height=500,
            xaxis_title='False Positive Rate',
            yaxis_title='True Positive Rate'
        )

        return fig.to_json()

    def save_model(self, filepath):
        """Save trained model to disk."""
        if not self.is_trained:
            raise ValueError("No trained model to save.")

        data = {
            'best_model_name': self.best_model_name,
            'best_model': self.best_model,
            'label_encoders': self.label_encoders,
            'target_encoder': self.target_encoder,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'target_col': self.target_col,
            'results': {k: {kk: vv for kk, vv in v.items() if kk != 'model'} 
                       for k, v in self.results.items()}
        }

        with open(filepath, 'wb') as f:
            pickle.dump(data, f)

    def load_model(self, filepath):
        """Load trained model from disk."""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)

        self.best_model_name = data['best_model_name']
        self.best_model = data['best_model']
        self.label_encoders = data['label_encoders']
        self.target_encoder = data['target_encoder']
        self.scaler = data['scaler']
        self.feature_names = data['feature_names']
        self.target_col = data.get('target_col')
        self.results = data['results']
        self.is_trained = True


def generate_synthetic_attrition_data(n_samples=1000):
    """Generate synthetic HR attrition dataset for demonstration."""
    np.random.seed(42)

    departments = ['Sales', 'R&D', 'HR', 'IT', 'Finance', 'Marketing', 'Operations']
    job_roles = ['Manager', 'Senior', 'Junior', 'Analyst', 'Engineer', 'Specialist', 'Director']
    education = ['High School', 'Bachelor', 'Master', 'PhD']

    data = {
        'Age': np.random.normal(35, 10, n_samples).clip(18, 65).astype(int),
        'Gender': np.random.choice(['Male', 'Female'], n_samples),
        'Department': np.random.choice(departments, n_samples),
        'JobRole': np.random.choice(job_roles, n_samples),
        'Education': np.random.choice(education, n_samples),
        'EducationLevel': np.random.randint(1, 5, n_samples),
        'MonthlyIncome': np.random.lognormal(8, 0.5, n_samples).astype(int),
        'DailyRate': np.random.randint(100, 1500, n_samples),
        'HourlyRate': np.random.randint(15, 100, n_samples),
        'PercentSalaryHike': np.random.randint(0, 25, n_samples),
        'TotalWorkingYears': np.random.exponential(10, n_samples).clip(0, 40).astype(int),
        'YearsAtCompany': np.random.exponential(5, n_samples).clip(0, 40).astype(int),
        'YearsInCurrentRole': np.random.exponential(3, n_samples).clip(0, 20).astype(int),
        'YearsSinceLastPromotion': np.random.exponential(2, n_samples).clip(0, 15).astype(int),
        'YearsWithCurrManager': np.random.exponential(3, n_samples).clip(0, 17).astype(int),
        'JobSatisfaction': np.random.randint(1, 5, n_samples),
        'EnvironmentSatisfaction': np.random.randint(1, 5, n_samples),
        'WorkLifeBalance': np.random.randint(1, 5, n_samples),
        'JobInvolvement': np.random.randint(1, 5, n_samples),
        'PerformanceRating': np.random.choice([3, 4], n_samples, p=[0.85, 0.15]),
        'OverTime': np.random.choice(['Yes', 'No'], n_samples, p=[0.3, 0.7]),
        'BusinessTravel': np.random.choice(['Non-Travel', 'Travel_Rarely', 'Travel_Frequently'], n_samples),
        'MaritalStatus': np.random.choice(['Single', 'Married', 'Divorced'], n_samples),
        'NumCompaniesWorked': np.random.poisson(2, n_samples).clip(0, 10),
        'TrainingTimesLastYear': np.random.poisson(3, n_samples).clip(0, 6),
        'StockOptionLevel': np.random.choice([0, 1, 2, 3], n_samples, p=[0.4, 0.3, 0.2, 0.1]),
        'DistanceFromHome': np.random.exponential(5, n_samples).clip(1, 30).astype(int),
        'Attrition': np.random.choice(['Yes', 'No'], n_samples, p=[0.16, 0.84])
    }

    df = pd.DataFrame(data)

    # Make attrition more realistic based on features
    for idx in df.index:
        score = 0
        if df.loc[idx, 'JobSatisfaction'] <= 2:
            score += 0.3
        if df.loc[idx, 'OverTime'] == 'Yes':
            score += 0.2
        if df.loc[idx, 'YearsSinceLastPromotion'] > 5:
            score += 0.15
        if df.loc[idx, 'MonthlyIncome'] < np.percentile(df['MonthlyIncome'], 25):
            score += 0.15
        if df.loc[idx, 'WorkLifeBalance'] <= 2:
            score += 0.1
        if df.loc[idx, 'EnvironmentSatisfaction'] <= 2:
            score += 0.1

        if score > 0.4 and df.loc[idx, 'Attrition'] == 'No':
            if np.random.random() < score:
                df.loc[idx, 'Attrition'] = 'Yes'
        elif score < 0.1 and df.loc[idx, 'Attrition'] == 'Yes':
            if np.random.random() < 0.5:
                df.loc[idx, 'Attrition'] = 'No'

    return df