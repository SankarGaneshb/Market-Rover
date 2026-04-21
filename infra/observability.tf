# --- Market-Rover Observability Infrastructure ---
# This file defines the Centralized SRE Dashboard in Google Cloud Monitoring.
# It provides a "single pane of glass" for API health, database performance, and CI/CD status.

resource "google_monitoring_dashboard" "market_rover_sre_dashboard" {
  dashboard_json = <<EOF
{
  "displayName": "Market-Rover v5 Global SRE Dashboard",
  "gridLayout": {
    "columns": "2",
    "widgets": [
      {
        "title": "Global API Request Volume (Cloud Run)",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"run.googleapis.com/request_count\" resource.type=\"cloud_run_revision\"",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_RATE",
                    "crossSeriesReducer": "REDUCE_SUM",
                    "alignmentPeriod": "60s"
                  }
                }
              },
              "plotType": "LINE"
            }
          ]
        }
      },
      {
        "title": "Global Error Rate (HTTP 5xx)",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"run.googleapis.com/request_count\" resource.type=\"cloud_run_revision\" metric.label.\"response_code_class\"=\"5xx\"",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_RATE",
                    "crossSeriesReducer": "REDUCE_SUM",
                    "alignmentPeriod": "60s"
                  }
                }
              },
              "plotType": "STACKED_BAR"
            }
          ]
        }
      },
      {
        "title": "Median Request Latency (ms)",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"run.googleapis.com/request_latencies\" resource.type=\"cloud_run_revision\"",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_PERCENTILE_50",
                    "crossSeriesReducer": "REDUCE_MEAN",
                    "alignmentPeriod": "60s"
                  }
                }
              },
              "plotType": "LINE"
            }
          ]
        }
      },
      {
        "title": "CPU Utilization (p99 Across Services)",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"run.googleapis.com/container/cpu/utilizations\" resource.type=\"cloud_run_revision\"",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_PERCENTILE_99",
                    "crossSeriesReducer": "REDUCE_MAX",
                    "alignmentPeriod": "60s"
                  }
                }
              },
              "plotType": "LINE"
            }
          ]
        }
      },
      {
        "title": "Database: Active Connections",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"cloudsql.googleapis.com/database/network/connections\" resource.type=\"cloud_sql_database\"",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_MEAN",
                    "alignmentPeriod": "60s"
                  }
                }
              },
              "plotType": "LINE"
            }
          ]
        }
      },
      {
        "title": "Database: Storage Usage (%)",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"cloudsql.googleapis.com/database/disk/utilization\" resource.type=\"cloud_sql_database\"",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_MEAN",
                    "alignmentPeriod": "60s"
                  }
                }
              },
              "plotType": "LINE"
            }
          ]
        }
      },
      {
        "title": "Cloud Build: Build Durations",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"cloudbuild.googleapis.com/builds/build_duration\" resource.type=\"build\"",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_MEAN",
                    "alignmentPeriod": "60s"
                  }
                }
              },
              "plotType": "LINE"
            }
          ]
        }
      },
      {
        "title": "Cloud Build: Success vs Failure Rate",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"cloudbuild.googleapis.com/builds/completed_builds\" resource.type=\"build\"",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_RATE",
                    "crossSeriesReducer": "REDUCE_SUM",
                    "alignmentPeriod": "60s"
                  }
                }
              },
              "plotType": "STACKED_BAR"
            }
          ]
        }
      }
    ]
  }
}
EOF
}

# --- Automated Alerting Policies ---

resource "google_monitoring_notification_channel" "hil_rover_webhook" {
  display_name = "HIL-Rover Mission Control (Webhook)"
  type         = "webhook"
  labels = {
    url = "https://hil-rover-9514347926.us-central1.run.app/api/alerts/gcp"
  }
}

resource "google_monitoring_alert_policy" "high_5xx_rate" {
  display_name = "Global 5xx Error Rate > 5% (Market-Rover)"
  combiner     = "OR"
  conditions {
    display_name = "Cloud Run 5xx Error Rate"
    condition_threshold {
      filter     = "metric.type=\"run.googleapis.com/request_count\" resource.type=\"cloud_run_revision\" metric.label.\"response_code_class\"=\"5xx\""
      duration   = "300s"
      comparison = "COMPARISON_GT"
      threshold_value = 0.05
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = [
    google_monitoring_notification_channel.hil_rover_webhook.name
  ]

  documentation {
    content   = "Market-Rover is experiencing a high volume of 5xx errors. Check the Global SRE Dashboard and Cloud Run logs."
    mime_type = "text/markdown"
  }
}
