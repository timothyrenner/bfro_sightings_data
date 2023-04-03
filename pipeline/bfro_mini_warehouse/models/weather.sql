{{ config(
    materialized="external",
    location=var('data_dir') + "/interim/weather.csv",
    format="csv",
    pre_hook="
        CREATE MACRO convert_str_null_to_null(col) AS 
        CASE WHEN col != 'null' THEN col ELSE NULL END
    "
) }}

WITH extracted_weather_fields AS (
    SELECT
        hexid,
        timestamp,
        data -> 'days' -> 0 ->> 'tempmax' AS temperature_high,
        data -> 'days' -> 0 ->> 'tempmin' AS temperature_low,
        data -> 'days' -> 0 ->> 'temp' AS temperature_mid,
        data -> 'days' -> 0 ->> 'dew' AS dew_point,
        data -> 'days' -> 0 ->> 'humidity' AS humidity,
        data -> 'days' -> 0 ->> 'cloudcover' AS cloud_cover,
        data -> 'days' -> 0 ->> 'moonphase' AS moon_phase,
        data -> 'days' -> 0 ->> 'precip' AS precip_intensity,
        data -> 'days' -> 0 ->> 'precipprob' AS precip_probability,
        data -> 'days' -> 0 ->> 'preciptype' AS precip_type,
        data -> 'days' -> 0 ->> 'pressure' AS pressure,
        data -> 'days' -> 0 ->> 'description' AS summary,
        data -> 'days' -> 0 ->> 'conditions' AS conditions,
        data -> 'days' -> 0 ->> 'uvindex' AS uv_index,
        data -> 'days' -> 0 ->> 'visibility' AS visibility,
        data -> 'days' -> 0 ->> 'winddir' AS wind_bearing,
        data -> 'days' -> 0 ->> 'windspeed' AS wind_speed,
    FROM
        {{ source("local_files", "weather_cache") }}
    WHERE data IS NOT NULL
)

SELECT
    hexid,
    timestamp,
    CONVERT_STR_NULL_TO_NULL(temperature_high)::FLOAT AS temperature_high,
    CONVERT_STR_NULL_TO_NULL(temperature_low)::FLOAT AS temperature_low,
    CONVERT_STR_NULL_TO_NULL(temperature_mid)::FLOAT AS temperature_mid,
    CONVERT_STR_NULL_TO_NULL(dew_point)::FLOAT AS dew_point,
    CONVERT_STR_NULL_TO_NULL(humidity)::FLOAT AS humidity,
    CONVERT_STR_NULL_TO_NULL(cloud_cover)::FLOAT AS cloud_cover,
    CONVERT_STR_NULL_TO_NULL(moon_phase)::FLOAT AS moon_phase,
    CONVERT_STR_NULL_TO_NULL(precip_intensity)::FLOAT AS precip_intensity,
    CONVERT_STR_NULL_TO_NULL(precip_probability)::FLOAT AS precip_probability,
    CONVERT_STR_NULL_TO_NULL(precip_type) AS precip_type,
    CONVERT_STR_NULL_TO_NULL(pressure)::FLOAT AS pressure,
    CONVERT_STR_NULL_TO_NULL(summary) AS summary,
    CONVERT_STR_NULL_TO_NULL(conditions) AS conditions,
    CONVERT_STR_NULL_TO_NULL(uv_index)::FLOAT AS uv_index,
    CONVERT_STR_NULL_TO_NULL(visibility)::FLOAT AS visibility,
    CONVERT_STR_NULL_TO_NULL(wind_bearing)::FLOAT AS wind_bearing,
    CONVERT_STR_NULL_TO_NULL(wind_speed)::FLOAT AS wind_speed,
FROM
    extracted_weather_fields
