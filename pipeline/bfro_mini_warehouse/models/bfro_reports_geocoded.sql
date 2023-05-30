{{
    config(
        materialized="external",
        location=var('data_dir') + "/processed/bfro_reports_geocoded.csv",
        format="csv"
    )
}}


SELECT
    -- Re-alias these columns to represent them as lower case in the CSV file.
    -- SQL sees them as lower cased anyway but should be that way in the final
    -- file as well.
    reports.observed AS observed,
    reports.location_details AS location_details,
    reports.county AS county,
    reports.state AS state,
    reports.season AS season,
    geo.title,
    geo.latitude,
    geo.longitude,
    COALESCE(STRFTIME(geo.timestamp, '%Y-%m-%d'), reports.date) AS date,
    COALESCE(reports.report_number, geo.number) AS number,
    COALESCE(reports.report_class, geo.classification) AS classification,
    geo.hexid,
    weather.temperature_high,
    weather.temperature_mid,
    weather.temperature_low,
    weather.dew_point,
    weather.humidity,
    weather.cloud_cover,
    weather.moon_phase,
    weather.precip_intensity,
    weather.precip_probability,
    weather.precip_type,
    weather.pressure,
    weather.summary,
    weather.conditions,
    weather.uv_index,
    weather.visibility,
    weather.wind_bearing,
    weather.wind_speed,
FROM
    {{ source("local_files", "geocoded_reports") }} AS geo
FULL OUTER JOIN
    {{ source("local_files", "bfro_reports") }} AS reports
    ON reports.report_number = geo.number
LEFT JOIN
    {{ ref("weather") }} AS weather
    ON geo.hexid = weather.hexid AND geo.timestamp = weather.timestamp