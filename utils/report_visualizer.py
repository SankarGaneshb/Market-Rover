"""
Report visualization utilities for Market-Rover 2.0
Generates interactive charts and exports to multiple formats
"""
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path


class ReportVisualizer:
    """Generate visualizations for portfolio analysis reports"""
    
    def __init__(self):
        """Initialize the visualizer with default settings"""
        self.color_scheme = {
            'positive': '#10b981',  # Green
            'negative': '#ef4444',  # Red
            'neutral': '#6b7280',   # Gray
            'background': '#1f2937',  # Dark background
            'text': '#f9fafb'  # Light text
        }
    
    def create_sentiment_pie_chart(self, sentiment_data: Dict[str, int]) -> go.Figure:
        """
        Create a pie chart showing sentiment distribution.
        
        Args:
            sentiment_data: Dictionary with counts {'positive': 10, 'negative': 5, 'neutral': 3}
            
        Returns:
            Plotly figure object
        """
        labels = []
        values = []
        colors = []
        
        for sentiment, count in sentiment_data.items():
            if count > 0:
                labels.append(sentiment.capitalize())
                values.append(count)
                colors.append(self.color_scheme.get(sentiment.lower(), '#gray'))
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,  # Donut chart
            marker=dict(colors=colors),
            textinfo='label+percent',
            textfont=dict(size=14),
            hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            title={
                'text': '📊 News Sentiment Distribution',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            showlegend=True,
            height=400,
            paper_bgcolor='white',
            plot_bgcolor='white'
        )
        
        return fig
    
    def create_portfolio_heatmap(self, stock_data: List[Dict]) -> go.Figure:
        """
        Create a heatmap showing portfolio health by stock.
        
        Args:
            stock_data: List of dicts with stock info [{'symbol': 'INFY', 'risk_score': 75, 'sentiment': 'negative'}]
            
        Returns:
            Plotly figure object
        """
        if not stock_data:
            return go.Figure()
        
        # Prepare data
        symbols = [s['symbol'] for s in stock_data]
        risk_scores = [s.get('risk_score', 50) for s in stock_data]
        sentiments = [s.get('sentiment', 'neutral') for s in stock_data]
        
        # Create color scale based on risk (0-100)
        colors = []
        for score in risk_scores:
            if score < 30:
                colors.append(self.color_scheme['positive'])
            elif score < 70:
                colors.append('#fbbf24')  # Yellow
            else:
                colors.append(self.color_scheme['negative'])
        
        shadow_scores = [s.get('shadow_score', 0) for s in stock_data]
        shadow_signals = [s.get('shadow_signals', '') for s in stock_data]
        
        # Combine customdata [sentiment, shadow_score, shadow_signal]
        custom_data_combined = list(zip(sentiments, shadow_scores, shadow_signals))
        
        fig = go.Figure(data=go.Bar(
            x=symbols,
            y=risk_scores,
            marker=dict(
                color=colors,
                line=dict(color='white', width=2)
            ),
            text=[f"{score}" for score in risk_scores],
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>Risk Score: %{y}<br>Shadow Score: %{customdata[1]} (%{customdata[2]})<br>Sentiment: %{customdata[0]}<extra></extra>',
            customdata=custom_data_combined
        ))
        
        fig.update_layout(
            title={
                'text': '🗺️ Portfolio Risk Heatmap',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            xaxis_title='Stock Symbol',
            yaxis_title='Risk Score (0-100)',
            yaxis=dict(range=[0, 100]),
            height=400,
            paper_bgcolor='white',
            plot_bgcolor='white',
            showlegend=False
        )
        
        # Add risk zones
        fig.add_hline(y=30, line_dash="dash", line_color="gray", annotation_text="Low Risk", annotation_position="right")
        fig.add_hline(y=70, line_dash="dash", line_color="gray", annotation_text="High Risk", annotation_position="right")
        
        return fig
    
    def create_risk_gauge(self, risk_score: float, stock_name: str) -> go.Figure:
        """
        Create a gauge chart for individual stock risk.
        
        Args:
            risk_score: Risk score 0-100
            stock_name: Name of the stock
            
        Returns:
            Plotly figure object
        """
        # Determine color based on risk
        if risk_score < 30:
            color = self.color_scheme['positive']
        elif risk_score < 70:
            color = '#fbbf24'
        else:
            color = self.color_scheme['negative']
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=risk_score,
            title={'text': f"{stock_name} Risk Level", 'font': {'size': 16}},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, 30], 'color': "lightgreen"},
                    {'range': [30, 70], 'color': "lightyellow"},
                    {'range': [70, 100], 'color': "lightcoral"}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': risk_score
                }
            }
        ))
        
        fig.update_layout(
            height=300,
            paper_bgcolor='white',
            font={'size': 14}
        )
        
        return fig
    
    def create_news_timeline(self, news_data: List[Dict]) -> go.Figure:
        """
        Create a timeline of news articles with sentiment markers.
        
        Args:
            news_data: List of news articles [{'date': datetime, 'title': str, 'sentiment': str, 'stock': str}]
            
        Returns:
            Plotly figure object
        """
        if not news_data:
            return go.Figure()
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(news_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Create scatter plot
        fig = go.Figure()
        
        for sentiment in ['positive', 'negative', 'neutral']:
            sentiment_df = df[df['sentiment'].str.lower() == sentiment]
            if not sentiment_df.empty:
                fig.add_trace(go.Scatter(
                    x=sentiment_df['date'],
                    y=sentiment_df['stock'],
                    mode='markers',
                    name=sentiment.capitalize(),
                    marker=dict(
                        size=12,
                        color=self.color_scheme.get(sentiment, '#gray'),
                        symbol='circle'
                    ),
                    text=sentiment_df['title'],
                    hovertemplate='<b>%{y}</b><br>%{text}<br>%{x|%b %d, %Y}<extra></extra>'
                ))
        
        fig.update_layout(
            title={
                'text': '📅 News Timeline',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            xaxis_title='Date',
            yaxis_title='Stock',
            height=400,
            paper_bgcolor='white',
            plot_bgcolor='white',
            hovermode='closest'
        )
        
        return fig
    
    def export_to_html(self, figures: List[go.Figure], report_text: str, output_path: Path) -> Path:
        """
        Export report with interactive charts to HTML.
        
        Args:
            figures: List of Plotly figures
            report_text: Text content of the report
            output_path: Path to save HTML file
            
        Returns:
            Path to saved HTML file
        """
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Market-Rover 2.0 Intelligence Report</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9fafb;
        }}
        h1 {{
            color: #1f2937;
            border-bottom: 3px solid #3b82f6;
            padding-bottom: 10px;
        }}
        .report-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .report-text {{
            background: white;
            padding: 30px;
            margin: 20px 0;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            line-height: 1.6;
        }}
        .footer {{
            text-align: center;
            color: #6b7280;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
        }}
    </style>
</head>
<body>
    <div class="report-header">
        <h1>🔍 Market-Rover Intelligence Report</h1>
        <p>Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
    </div>
    
    <div class="chart-container">
        <h2>📊 Visual Analytics</h2>
"""
        
        # Add each figure
        for i, fig in enumerate(figures):
            fig_html = fig.to_html(full_html=False, include_plotlyjs=False)
            html_content += f'<div id="chart{i}">{fig_html}</div>\n'
        
        html_content += """
    </div>
    
    <div class="report-text">
        <h2>📄 Detailed Analysis</h2>
"""
        html_content += f"<pre>{report_text}</pre>"
        
        html_content += """
    </div>
    
    <div class="footer">
        <p>Generated by Market-Rover - AI-Powered Stock Intelligence System</p>
    </div>
</body>
</html>
"""
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path


    def create_correlation_heatmap(self, matrix: pd.DataFrame) -> go.Figure:
        """
        Create a masked correlation heatmap (lower triangle only).
        
        Args:
            matrix: Correlation matrix DataFrame
            
        Returns:
            Plotly figure object
        """
        import numpy as np
        
        # Create mask
        mask = np.triu(np.ones_like(matrix, dtype=bool))
        
        # Apply mask by setting upper triangle to None (Plotly handles None as transparency in heatmap usually, 
        # or we might need to rely on custom text or filtering values. 
        # Actually Plotly Heatmap doesn't support 'mask' natively like Seaborn.
        # We must set values to None or NaN.)
        
        # Convert to float for safety (avoid int issues with None)
        matrix_masked = matrix.where(~mask, None)

        fig = go.Figure(data=go.Heatmap(
            z=matrix_masked.values,
            x=matrix_masked.columns,
            y=matrix_masked.index,
            text=matrix_masked.values,
            texttemplate="%{text:.2f}",
            textfont={"size": 10},
            colorscale='RdBu_r',
            zmin=-1, 
            zmax=1,
            xgap=1, 
            ygap=1,
            hoverongaps=False
        ))
        
        fig.update_layout(
            title={
                'text': '🔗 Correlation Heatmap (Lower Triangle)',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            height=500,
            width=500,
            yaxis_autorange='reversed', # Upper left origin
            paper_bgcolor='white',
            plot_bgcolor='white'
        )
        
        return fig

    def export_to_csv(data: List[Dict], output_path: Path) -> Path:
        """
        Export portfolio data to CSV format.
        
        Args:
            data: List of stock data dictionaries
            output_path: Path to save CSV file
            
        Returns:
            Path to saved CSV file
        """
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
        return output_path
