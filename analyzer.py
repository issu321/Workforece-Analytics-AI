"""
Workforce Analytics and Analysis Engine.
Handles all HR analytics, insights, forecasting, and retention recommendations.
"""

import json
import warnings
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

warnings.filterwarnings('ignore')


class WorkforceAnalyzer:
    """Comprehensive workforce analytics engine."""

    def __init__(self, df=None):
        self.df = df
        self.analytics = {}
        self.insights = []

    def set_data(self, df):
        """Set the dataset for analysis."""
        self.df = df.copy()
        self.analytics = {}
        self.insights = []

    def _find_attrition_column(self):
        """Find the attrition column in the dataframe."""
        for col in ['Attrition', 'attrition', 'Left', 'left', 'turnover', 'Turnover']:
            if col in self.df.columns:
                return col
        return None

    def _calculate_attrition_rate(self, df_subset):
        """Calculate attrition rate for a subset."""
        if df_subset is None or len(df_subset) == 0:
            return 0.0
        attr_col = self._find_attrition_column()
        if attr_col is None:
            return 0.0
        attr_series = df_subset[attr_col]
        if attr_series.dtype == 'object':
            yes_count = attr_series.astype(str).str.lower().isin(['yes', '1', 'true', 'left']).sum()
        else:
            yes_count = (attr_series == 1).sum()
        return round(yes_count / len(df_subset) * 100, 2)

    # ===================== DESCRIPTIVE ANALYTICS =====================

    def workforce_overview(self):
        """Generate workforce overview statistics."""
        if self.df is None or self.df.empty:
            return {}

        df = self.df
        overview = {
            'total_employees': len(df),
            'total_departments': df.get('Department', pd.Series()).nunique() if 'Department' in df.columns else 0,
            'total_job_roles': df.get('JobRole', pd.Series()).nunique() if 'JobRole' in df.columns else 0,
            'avg_age': round(df.get('Age', pd.Series()).mean(), 1) if 'Age' in df.columns else None,
            'avg_income': round(df.get('MonthlyIncome', pd.Series()).mean(), 0) if 'MonthlyIncome' in df.columns else None,
            'avg_tenure': round(df.get('YearsAtCompany', pd.Series()).mean(), 1) if 'YearsAtCompany' in df.columns else None,
            'attrition_rate': self._get_attrition_rate(),
            'gender_distribution': self._get_gender_distribution(),
            'department_distribution': self._get_department_distribution(),
            'education_distribution': self._get_education_distribution()
        }
        return overview

    def _get_attrition_rate(self):
        """Calculate overall attrition rate."""
        return self._calculate_attrition_rate(self.df)

    def _get_gender_distribution(self):
        """Get gender distribution."""
        if 'Gender' in self.df.columns:
            return self.df['Gender'].value_counts().to_dict()
        return {}

    def _get_department_distribution(self):
        """Get department distribution."""
        if 'Department' in self.df.columns:
            return self.df['Department'].value_counts().to_dict()
        return {}

    def _get_education_distribution(self):
        """Get education distribution."""
        if 'Education' in self.df.columns:
            return self.df['Education'].value_counts().to_dict()
        elif 'EducationLevel' in self.df.columns:
            return self.df['EducationLevel'].value_counts().to_dict()
        return {}

    # ===================== DEPARTMENT ANALYTICS =====================

    def department_analytics(self):
        """Analyze department-level metrics."""
        if self.df is None or 'Department' not in self.df.columns:
            return {}

        df = self.df
        dept_stats = {}

        for dept in df['Department'].unique():
            dept_df = df[df['Department'] == dept]

            stats_dict = {
                'employee_count': len(dept_df),
                'avg_age': round(dept_df.get('Age', pd.Series()).mean(), 1) if 'Age' in dept_df.columns else None,
                'avg_income': round(dept_df.get('MonthlyIncome', pd.Series()).mean(), 0) if 'MonthlyIncome' in dept_df.columns else None,
                'avg_tenure': round(dept_df.get('YearsAtCompany', pd.Series()).mean(), 1) if 'YearsAtCompany' in dept_df.columns else None,
                'avg_satisfaction': round(dept_df.get('JobSatisfaction', pd.Series()).mean(), 2) if 'JobSatisfaction' in dept_df.columns else None,
                'avg_performance': round(dept_df.get('PerformanceRating', pd.Series()).mean(), 2) if 'PerformanceRating' in dept_df.columns else None,
                'attrition_rate': self._calculate_attrition_rate(dept_df)
            }

            dept_stats[dept] = stats_dict

        return dept_stats

    # ===================== PERFORMANCE ANALYTICS =====================

    def performance_analytics(self):
        """Analyze employee performance metrics."""
        if self.df is None:
            return {}

        df = self.df
        perf = {}

        if 'PerformanceRating' in df.columns:
            perf['rating_distribution'] = df['PerformanceRating'].value_counts().sort_index().to_dict()
            perf['avg_rating'] = round(df['PerformanceRating'].mean(), 2)

        if 'JobSatisfaction' in df.columns:
            perf['satisfaction_distribution'] = df['JobSatisfaction'].value_counts().sort_index().to_dict()
            perf['avg_satisfaction'] = round(df['JobSatisfaction'].mean(), 2)

        if 'WorkLifeBalance' in df.columns:
            perf['worklife_distribution'] = df['WorkLifeBalance'].value_counts().sort_index().to_dict()
            perf['avg_worklife'] = round(df['WorkLifeBalance'].mean(), 2)

        # High performers
        if 'PerformanceRating' in df.columns:
            high_perf_threshold = df['PerformanceRating'].quantile(0.75)
            high_performers = df[df['PerformanceRating'] >= high_perf_threshold]
            perf['high_performer_count'] = len(high_performers)
            perf['high_performer_pct'] = round(len(high_performers) / len(df) * 100, 1)

        # Underperformers
        if 'PerformanceRating' in df.columns:
            low_perf_threshold = df['PerformanceRating'].quantile(0.25)
            underperformers = df[df['PerformanceRating'] <= low_perf_threshold]
            perf['underperformer_count'] = len(underperformers)
            perf['underperformer_pct'] = round(len(underperformers) / len(df) * 100, 1)

        return perf

    # ===================== SALARY ANALYTICS =====================

    def salary_analytics(self):
        """Analyze salary distribution and equity."""
        if self.df is None or 'MonthlyIncome' not in self.df.columns:
            return {}

        df = self.df
        income = df['MonthlyIncome']

        salary_stats = {
            'mean': round(income.mean(), 0),
            'median': round(income.median(), 0),
            'std': round(income.std(), 0),
            'min': round(income.min(), 0),
            'max': round(income.max(), 0),
            'q25': round(income.quantile(0.25), 0),
            'q75': round(income.quantile(0.75), 0),
            'pay_gap_by_gender': {},
            'pay_by_department': {},
            'pay_by_jobrole': {}
        }

        if 'Gender' in df.columns:
            for gender in df['Gender'].unique():
                gender_income = df[df['Gender'] == gender]['MonthlyIncome']
                salary_stats['pay_gap_by_gender'][gender] = round(gender_income.mean(), 0)

        if 'Department' in df.columns:
            for dept in df['Department'].unique():
                dept_income = df[df['Department'] == dept]['MonthlyIncome']
                salary_stats['pay_by_department'][dept] = round(dept_income.mean(), 0)

        if 'JobRole' in df.columns:
            for role in df['JobRole'].unique():
                role_income = df[df['JobRole'] == role]['MonthlyIncome']
                salary_stats['pay_by_jobrole'][role] = round(role_income.mean(), 0)

        return salary_stats

    # ===================== ADVANCED SCORES =====================

    def calculate_advanced_scores(self):
        """Calculate workforce health and engagement scores."""
        if self.df is None:
            return {}

        df = self.df
        scores = {}

        # Workforce Health Score (0-100)
        health_components = []

        if 'JobSatisfaction' in df.columns:
            sat_score = (df['JobSatisfaction'].mean() / 4) * 100
            health_components.append(sat_score)

        if 'EnvironmentSatisfaction' in df.columns:
            env_score = (df['EnvironmentSatisfaction'].mean() / 4) * 100
            health_components.append(env_score)

        if 'WorkLifeBalance' in df.columns:
            wlb_score = (df['WorkLifeBalance'].mean() / 4) * 100
            health_components.append(wlb_score)

        if 'PerformanceRating' in df.columns:
            perf_score = ((df['PerformanceRating'].mean() - 3) / 1) * 100
            perf_score = max(0, min(100, perf_score))
            health_components.append(perf_score)

        attrition_rate = self._get_attrition_rate()
        retention_score = max(0, 100 - attrition_rate * 5)
        health_components.append(retention_score)

        if health_components:
            scores['workforce_health_score'] = round(np.mean(health_components), 1)

        # Employee Engagement Score
        engagement_components = []
        if 'JobInvolvement' in df.columns:
            engagement_components.append((df['JobInvolvement'].mean() / 4) * 100)
        if 'JobSatisfaction' in df.columns:
            engagement_components.append((df['JobSatisfaction'].mean() / 4) * 100)
        if 'EnvironmentSatisfaction' in df.columns:
            engagement_components.append((df['EnvironmentSatisfaction'].mean() / 4) * 100)

        if engagement_components:
            scores['engagement_score'] = round(np.mean(engagement_components), 1)

        # Department Stability Score
        if 'Department' in df.columns:
            dept_stability = []
            for dept in df['Department'].unique():
                dept_df = df[df['Department'] == dept]
                dept_attrition = self._calculate_attrition_rate(dept_df)
                dept_stability.append(max(0, 100 - dept_attrition * 3))
            scores['department_stability_score'] = round(np.mean(dept_stability), 1)

        # Workforce Risk Index
        risk_components = []
        if attrition_rate > 10:
            risk_components.append(min(100, attrition_rate * 5))
        if 'JobSatisfaction' in df.columns and df['JobSatisfaction'].mean() < 2.5:
            risk_components.append(70)
        if 'WorkLifeBalance' in df.columns and df['WorkLifeBalance'].mean() < 2.5:
            risk_components.append(60)

        if risk_components:
            scores['workforce_risk_index'] = round(np.mean(risk_components), 1)
        else:
            scores['workforce_risk_index'] = round(attrition_rate * 3, 1)

        # Retention Effectiveness
        scores['retention_effectiveness'] = round(max(0, 100 - attrition_rate * 4), 1)

        # Productivity Score
        productivity_components = []
        if 'PerformanceRating' in df.columns:
            productivity_components.append((df['PerformanceRating'].mean() / 4) * 100)
        if 'YearsAtCompany' in df.columns:
            exp_score = min(100, (df['YearsAtCompany'].mean() / 10) * 100)
            productivity_components.append(exp_score)
        if 'TrainingTimesLastYear' in df.columns:
            training_score = min(100, (df['TrainingTimesLastYear'].mean() / 5) * 100)
            productivity_components.append(training_score)

        if productivity_components:
            scores['productivity_score'] = round(np.mean(productivity_components), 1)

        return scores

    # ===================== RETENTION RECOMMENDATIONS =====================

    def generate_retention_recommendations(self, predictions=None):
        """Generate data-driven retention recommendations."""
        if self.df is None:
            return []

        recommendations = []
        df = self.df
        attr_col = self._find_attrition_column()

        if attr_col:
            # Department-level attrition
            if 'Department' in df.columns:
                for dept in df['Department'].unique():
                    dept_df = df[df['Department'] == dept]
                    dept_attr = self._calculate_attrition_rate(dept_df)

                    if dept_attr > 20:
                        recommendations.append({
                            'category': 'Department Risk',
                            'priority': 'High',
                            'target': dept,
                            'issue': f'High attrition rate of {dept_attr:.1f}%',
                            'recommendation': f'Conduct exit interviews in {dept} department. Review workload distribution and management practices.',
                            'action_plan': [
                                f'Schedule 1-on-1 meetings with all {dept} employees',
                                'Audit workload and overtime hours',
                                'Review department manager effectiveness',
                                'Implement team-building initiatives'
                            ]
                        })

            # Salary-related attrition
            if 'MonthlyIncome' in df.columns:
                low_income = df[df['MonthlyIncome'] < df['MonthlyIncome'].quantile(0.25)]
                low_income_attr = self._calculate_attrition_rate(low_income)

                if low_income_attr > 15:
                    recommendations.append({
                        'category': 'Compensation',
                        'priority': 'High',
                        'target': 'Low-income employees',
                        'issue': f'{low_income_attr:.1f}% attrition among bottom 25% earners',
                        'recommendation': 'Review compensation structure. Consider market-rate adjustments for underpaid roles.',
                        'action_plan': [
                            'Conduct salary benchmarking analysis',
                            'Identify roles below market rate',
                            'Plan phased salary adjustments',
                            'Introduce retention bonuses for critical roles'
                        ]
                    })

            # Satisfaction-related
            if 'JobSatisfaction' in df.columns:
                low_sat = df[df['JobSatisfaction'] <= 2]
                if len(low_sat) > len(df) * 0.15:
                    recommendations.append({
                        'category': 'Employee Satisfaction',
                        'priority': 'Medium',
                        'target': 'Low satisfaction employees',
                        'issue': f'{len(low_sat)} employees ({len(low_sat)/len(df)*100:.1f}%) report low job satisfaction',
                        'recommendation': 'Implement employee satisfaction improvement programs. Address common pain points.',
                        'action_plan': [
                            'Distribute anonymous satisfaction survey',
                            'Identify top 3 dissatisfaction drivers',
                            'Create action committees per department',
                            'Track satisfaction quarterly'
                        ]
                    })

            # Overtime-related
            if 'OverTime' in df.columns:
                ot_yes = df[df['OverTime'].astype(str).str.lower().isin(['yes', '1', 'true'])]
                ot_attr = self._calculate_attrition_rate(ot_yes)

                if ot_attr > 20:
                    recommendations.append({
                        'category': 'Workload Management',
                        'priority': 'High',
                        'target': 'Overtime employees',
                        'issue': f'{ot_attr:.1f}% attrition among employees working overtime',
                        'recommendation': 'Reduce mandatory overtime. Hire additional staff or redistribute workload.',
                        'action_plan': [
                            'Audit overtime patterns by department',
                            'Hire temporary staff for peak periods',
                            'Implement flexible scheduling',
                            'Review project timelines and resource allocation'
                        ]
                    })

            # Promotion delay
            if 'YearsSinceLastPromotion' in df.columns:
                no_promo = df[df['YearsSinceLastPromotion'] > 5]
                no_promo_attr = self._calculate_attrition_rate(no_promo)

                if no_promo_attr > 15:
                    recommendations.append({
                        'category': 'Career Growth',
                        'priority': 'Medium',
                        'target': 'Long-tenure without promotion',
                        'issue': f'{no_promo_attr:.1f}% attrition among employees with 5+ years without promotion',
                        'recommendation': 'Create clear career progression paths. Accelerate promotion cycles for high performers.',
                        'action_plan': [
                            'Map career ladders for all roles',
                            'Implement quarterly promotion reviews',
                            'Create mentorship programs',
                            'Offer lateral moves for growth'
                        ]
                    })

        # If no specific issues found
        if not recommendations:
            recommendations.append({
                'category': 'General',
                'priority': 'Low',
                'target': 'All employees',
                'issue': 'No critical retention issues detected',
                'recommendation': 'Continue monitoring workforce metrics. Maintain current retention strategies.',
                'action_plan': [
                    'Continue quarterly satisfaction surveys',
                    'Maintain competitive compensation',
                    'Invest in employee development',
                    'Celebrate employee achievements'
                ]
            })

        return recommendations

    # ===================== AI INSIGHTS =====================

    def generate_insights(self):
        """Generate AI-driven insights from workforce data."""
        if self.df is None:
            return []

        insights = []
        df = self.df
        attr_col = self._find_attrition_column()

        if attr_col:
            # Top attrition driver
            if 'OverTime' in df.columns:
                ot_yes = df[df['OverTime'].astype(str).str.lower().isin(['yes', '1', 'true'])]
                ot_no = df[~df['OverTime'].astype(str).str.lower().isin(['yes', '1', 'true'])]

                ot_attr = self._calculate_attrition_rate(ot_yes)
                no_ot_attr = self._calculate_attrition_rate(ot_no)

                if ot_attr > no_ot_attr * 1.5:
                    insights.append({
                        'type': 'Attrition Driver',
                        'severity': 'High',
                        'insight': f'Overtime is a major attrition driver. Employees working overtime have {ot_attr:.1f}% attrition vs {no_ot_attr:.1f}% for others.',
                        'recommendation': 'Review overtime policies and workload distribution immediately.'
                    })

            # Income correlation
            if 'MonthlyIncome' in df.columns:
                low_income = df[df['MonthlyIncome'] < df['MonthlyIncome'].median()]
                high_income = df[df['MonthlyIncome'] >= df['MonthlyIncome'].median()]

                low_attr = self._calculate_attrition_rate(low_income)
                high_attr = self._calculate_attrition_rate(high_income)

                if low_attr > high_attr * 1.5:
                    insights.append({
                        'type': 'Compensation Risk',
                        'severity': 'High',
                        'insight': f'Lower-paid employees show {low_attr:.1f}% attrition vs {high_attr:.1f}% for higher-paid employees.',
                        'recommendation': 'Review compensation equity and consider market adjustments.'
                    })

            # Satisfaction correlation
            if 'JobSatisfaction' in df.columns:
                low_sat = df[df['JobSatisfaction'] <= 2]
                high_sat = df[df['JobSatisfaction'] >= 4]

                low_sat_attr = self._calculate_attrition_rate(low_sat)
                high_sat_attr = self._calculate_attrition_rate(high_sat)

                if low_sat_attr > high_sat_attr * 2:
                    insights.append({
                        'type': 'Satisfaction Risk',
                        'severity': 'Critical',
                        'insight': f'Low job satisfaction strongly correlates with attrition: {low_sat_attr:.1f}% vs {high_sat_attr:.1f}% for satisfied employees.',
                        'recommendation': 'Prioritize employee satisfaction improvement initiatives.'
                    })

        # Department insights
        if 'Department' in df.columns and 'MonthlyIncome' in df.columns:
            dept_avg = df.groupby('Department')['MonthlyIncome'].mean()
            max_dept = dept_avg.idxmax()
            min_dept = dept_avg.idxmin()
            gap = (dept_avg.max() - dept_avg.min()) / dept_avg.mean() * 100

            if gap > 30:
                insights.append({
                    'type': 'Pay Equity',
                    'severity': 'Medium',
                    'insight': f'Significant pay gap between departments: {max_dept} averages ${dept_avg.max():.0f} vs {min_dept} at ${dept_avg.min():.0f}.',
                    'recommendation': 'Review department compensation structures for equity.'
                })

        # Age distribution insight
        if 'Age' in df.columns:
            avg_age = df['Age'].mean()
            if avg_age > 45:
                insights.append({
                    'type': 'Aging Workforce',
                    'severity': 'Medium',
                    'insight': f'Average employee age is {avg_age:.1f} years. Succession planning is critical.',
                    'recommendation': 'Develop knowledge transfer programs and succession plans.'
                })
            elif avg_age < 28:
                insights.append({
                    'type': 'Young Workforce',
                    'severity': 'Low',
                    'insight': f'Average employee age is {avg_age:.1f} years. High growth potential but retention risk.',
                    'recommendation': 'Invest in career development and mentorship programs.'
                })

        self.insights = insights
        return insights

    # ===================== FORECASTING =====================

    def workforce_forecast(self, periods=12):
        """Forecast future workforce trends using time series."""
        if self.df is None:
            return {}

        current_attrition = self._get_attrition_rate()
        total_employees = len(self.df)

        forecast = {
            'periods': periods,
            'attrition_forecast': [],
            'workforce_size_forecast': [],
            'hiring_needs': []
        }

        current_size = total_employees

        for month in range(1, periods + 1):
            projected_attrition = max(5, current_attrition * (0.98 ** month) + np.random.normal(0, 0.5))
            projected_attrition = max(0, min(50, projected_attrition))

            departures = int(current_size * projected_attrition / 100 / 12)
            hiring_need = departures + int(total_employees * 0.02 / 12)
            current_size = current_size - departures + hiring_need

            forecast['attrition_forecast'].append({
                'month': month,
                'projected_attrition_rate': round(projected_attrition, 2),
                'projected_departures': departures
            })

            forecast['workforce_size_forecast'].append({
                'month': month,
                'projected_size': current_size
            })

            forecast['hiring_needs'].append({
                'month': month,
                'hiring_needed': hiring_need
            })

        return forecast

    # ===================== CHART GENERATION =====================

    def get_department_chart(self):
        """Generate department distribution chart."""
        if self.df is None or 'Department' not in self.df.columns:
            return None

        counts = self.df['Department'].value_counts()
        fig = px.pie(values=counts.values, names=counts.index, 
                     title='Employee Distribution by Department',
                     template='plotly_dark',
                     color_discrete_sequence=px.colors.sequential.Plasma)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=450)
        return fig.to_json()

    def get_attrition_heatmap(self):
        """Generate attrition heatmap by department and job role."""
        if self.df is None:
            return None

        dept_col = 'Department' if 'Department' in self.df.columns else None
        role_col = 'JobRole' if 'JobRole' in self.df.columns else None
        attr_col = self._find_attrition_column()

        if not dept_col or not attr_col:
            return None

        if role_col:
            # Create crosstab
            df_copy = self.df.copy()
            if df_copy[attr_col].dtype == 'object':
                df_copy[attr_col] = df_copy[attr_col].astype(str).str.lower().map({'yes': 1, 'no': 0, '1': 1, '0': 0}).fillna(0)

            try:
                pivot = df_copy.groupby([dept_col, role_col])[attr_col].mean().unstack(fill_value=0) * 100

                fig = px.imshow(pivot, 
                               labels=dict(x='Job Role', y='Department', color='Attrition %'),
                               title='Attrition Rate Heatmap: Department vs Job Role',
                               template='plotly_dark',
                               color_continuous_scale='Reds')
                fig.update_layout(height=500)
                return fig.to_json()
            except Exception:
                return None
        else:
            dept_attr = self.df.groupby(dept_col).apply(
                lambda x: self._calculate_attrition_rate(x)
            )
            fig = px.bar(x=dept_attr.index, y=dept_attr.values,
                        title='Attrition Rate by Department',
                        template='plotly_dark',
                        labels={'x': 'Department', 'y': 'Attrition Rate (%)'},
                        color=dept_attr.values,
                        color_continuous_scale='Reds')
            fig.update_layout(height=450)
            return fig.to_json()

    def get_salary_distribution_chart(self):
        """Generate salary distribution chart."""
        if self.df is None or 'MonthlyIncome' not in self.df.columns:
            return None

        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=self.df['MonthlyIncome'],
            nbinsx=30,
            marker_color='#6366f1',
            opacity=0.8,
            name='Salary Distribution'
        ))

        fig.add_vline(x=self.df['MonthlyIncome'].mean(), line_dash="dash", 
                     line_color="#10b981", annotation_text=f"Mean: ${self.df['MonthlyIncome'].mean():.0f}")
        fig.add_vline(x=self.df['MonthlyIncome'].median(), line_dash="dash", 
                     line_color="#f59e0b", annotation_text=f"Median: ${self.df['MonthlyIncome'].median():.0f}")

        fig.update_layout(
            title='Salary Distribution',
            template='plotly_dark',
            xaxis_title='Monthly Income ($)',
            yaxis_title='Count',
            height=450
        )
        return fig.to_json()

    def get_satisfaction_chart(self):
        """Generate satisfaction metrics chart."""
        if self.df is None:
            return None

        satisfaction_cols = [c for c in ['JobSatisfaction', 'EnvironmentSatisfaction', 
                                         'WorkLifeBalance', 'JobInvolvement'] if c in self.df.columns]

        if not satisfaction_cols:
            return None

        fig = go.Figure()
        colors = ['#6366f1', '#10b981', '#f59e0b', '#ef4444']

        for i, col in enumerate(satisfaction_cols):
            counts = self.df[col].value_counts().sort_index()
            fig.add_trace(go.Bar(
                x=[f'Level {int(k)}' for k in counts.index],
                y=counts.values,
                name=col.replace('Satisfaction', ' Sat').replace('Balance', ' Balance'),
                marker_color=colors[i % len(colors)]
            ))

        fig.update_layout(
            title='Employee Satisfaction Distribution',
            template='plotly_dark',
            barmode='group',
            xaxis_title='Rating Level',
            yaxis_title='Count',
            height=450
        )
        return fig.to_json()

    def get_workforce_forecast_chart(self, forecast_data):
        """Generate workforce forecast visualization."""
        if not forecast_data:
            return None

        months = [f'M{i}' for i in range(1, forecast_data['periods'] + 1)]
        attrition = [d['projected_attrition_rate'] for d in forecast_data['attrition_forecast']]
        size = [d['projected_size'] for d in forecast_data['workforce_size_forecast']]
        hiring = [d['hiring_needed'] for d in forecast_data['hiring_needs']]

        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Projected Attrition Rate (%)', 'Projected Workforce Size'),
            vertical_spacing=0.15
        )

        fig.add_trace(go.Scatter(x=months, y=attrition, mode='lines+markers',
                                name='Attrition %', line=dict(color='#ef4444')), row=1, col=1)
        fig.add_trace(go.Scatter(x=months, y=size, mode='lines+markers',
                                name='Workforce Size', line=dict(color='#6366f1')), row=2, col=1)

        fig.update_layout(
            title='Workforce Forecast (Next 12 Months)',
            template='plotly_dark',
            height=700,
            showlegend=False
        )
        return fig.to_json()

    def get_age_distribution_chart(self):
        """Generate age distribution chart."""
        if self.df is None or 'Age' not in self.df.columns:
            return None

        fig = px.histogram(self.df, x='Age', nbins=20,
                          title='Age Distribution',
                          template='plotly_dark',
                          color_discrete_sequence=['#6366f1'])
        fig.update_layout(height=450, xaxis_title='Age', yaxis_title='Count')
        return fig.to_json()

    def get_gender_chart(self):
        """Generate gender distribution chart."""
        if self.df is None or 'Gender' not in self.df.columns:
            return None

        counts = self.df['Gender'].value_counts()
        if len(counts) == 0:
            return None

        fig = px.pie(values=counts.values, names=counts.index,
                    title='Gender Distribution',
                    template='plotly_dark',
                    hole=0.4,
                    color_discrete_sequence=['#6366f1', '#ec4899', '#10b981'])
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400)
        return fig.to_json()

    def get_tenure_chart(self):
        """Generate tenure distribution chart."""
        if self.df is None or 'YearsAtCompany' not in self.df.columns:
            return None

        fig = px.histogram(self.df, x='YearsAtCompany', nbins=15,
                          title='Employee Tenure Distribution',
                          template='plotly_dark',
                          color_discrete_sequence=['#10b981'])
        fig.update_layout(height=450, xaxis_title='Years at Company', yaxis_title='Count')
        return fig.to_json()

    def get_correlation_heatmap(self):
        """Generate correlation heatmap for numeric features."""
        if self.df is None:
            return None

        numeric_df = self.df.select_dtypes(include=[np.number])
        if numeric_df.empty or len(numeric_df.columns) < 2:
            return None

        corr = numeric_df.corr()
        fig = px.imshow(corr, text_auto='.2f',
                       title='Feature Correlation Heatmap',
                       template='plotly_dark',
                       color_continuous_scale='RdBu_r',
                       aspect='auto')
        fig.update_layout(height=600)
        return fig.to_json()
