import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import ble_client, sensor, binary_sensor, text_sensor
from esphome.const import (
    CONF_ID,
    DEVICE_CLASS_WEIGHT,
    STATE_CLASS_MEASUREMENT,
    UNIT_KILOGRAM,
)

DEPENDENCIES = ["ble_client"]
AUTO_LOAD = ["sensor", "binary_sensor", "text_sensor"]

CONF_BLE_CLIENT_ID = "ble_client_id"
CONF_MIN_WEIGHT = "min_weight"
CONF_HEIGHT = "height"
CONF_AGE = "age"
CONF_GENDER = "gender"
CONF_WEIGHT_SENSOR = "weight_sensor"
CONF_WEIGHT_LBS_SENSOR = "weight_lbs_sensor"
CONF_IMPEDANCE_SENSOR = "impedance_sensor"
CONF_BMI_SENSOR = "bmi_sensor"
CONF_BODY_FAT_SENSOR = "body_fat_sensor"
CONF_MUSCLE_MASS_SENSOR = "muscle_mass_sensor"
CONF_WATER_PCT_SENSOR = "water_pct_sensor"
CONF_BONE_MASS_SENSOR = "bone_mass_sensor"
CONF_BMR_SENSOR = "bmr_sensor"
CONF_VISCERAL_FAT_SENSOR = "visceral_fat_sensor"
CONF_ACTIVE_SENSOR = "active_sensor"
CONF_LAST_READING_SENSOR = "last_reading_sensor"

qn_scale_ns = cg.esphome_ns.namespace("qn_scale")
QNScale = qn_scale_ns.class_(
    "QNScale", ble_client.BLEClientNode, cg.Component
)

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.declare_id(QNScale),
        cv.Required(CONF_BLE_CLIENT_ID): cv.use_id(ble_client.BLEClient),
        cv.Optional(CONF_MIN_WEIGHT, default=20.0): cv.float_,
        cv.Optional(CONF_HEIGHT, default=175.0): cv.float_,
        cv.Optional(CONF_AGE, default=30): cv.int_,
        cv.Optional(CONF_GENDER, default="male"): cv.one_of("male", "female", lower=True),
        cv.Optional(CONF_WEIGHT_SENSOR): sensor.sensor_schema(
            unit_of_measurement=UNIT_KILOGRAM,
            accuracy_decimals=2,
            device_class=DEVICE_CLASS_WEIGHT,
            state_class=STATE_CLASS_MEASUREMENT,
            icon="mdi:scale-bathroom",
        ),
        cv.Optional(CONF_WEIGHT_LBS_SENSOR): sensor.sensor_schema(
            unit_of_measurement="lbs",
            accuracy_decimals=1,
            device_class=DEVICE_CLASS_WEIGHT,
            state_class=STATE_CLASS_MEASUREMENT,
            icon="mdi:scale-bathroom",
        ),
        cv.Optional(CONF_IMPEDANCE_SENSOR): sensor.sensor_schema(
            unit_of_measurement="\u03A9",
            accuracy_decimals=0,
            state_class=STATE_CLASS_MEASUREMENT,
            icon="mdi:flash-triangle-outline",
        ),
        cv.Optional(CONF_BMI_SENSOR): sensor.sensor_schema(
            unit_of_measurement="BMI",
            accuracy_decimals=1,
            state_class=STATE_CLASS_MEASUREMENT,
            icon="mdi:human",
        ),
        cv.Optional(CONF_BODY_FAT_SENSOR): sensor.sensor_schema(
            unit_of_measurement="%",
            accuracy_decimals=1,
            state_class=STATE_CLASS_MEASUREMENT,
            icon="mdi:percent",
        ),
        cv.Optional(CONF_MUSCLE_MASS_SENSOR): sensor.sensor_schema(
            unit_of_measurement=UNIT_KILOGRAM,
            accuracy_decimals=1,
            state_class=STATE_CLASS_MEASUREMENT,
            icon="mdi:arm-flex",
        ),
        cv.Optional(CONF_WATER_PCT_SENSOR): sensor.sensor_schema(
            unit_of_measurement="%",
            accuracy_decimals=1,
            state_class=STATE_CLASS_MEASUREMENT,
            icon="mdi:water-percent",
        ),
        cv.Optional(CONF_BONE_MASS_SENSOR): sensor.sensor_schema(
            unit_of_measurement=UNIT_KILOGRAM,
            accuracy_decimals=1,
            state_class=STATE_CLASS_MEASUREMENT,
            icon="mdi:bone",
        ),
        cv.Optional(CONF_BMR_SENSOR): sensor.sensor_schema(
            unit_of_measurement="kcal",
            accuracy_decimals=0,
            state_class=STATE_CLASS_MEASUREMENT,
            icon="mdi:fire",
        ),
        cv.Optional(CONF_VISCERAL_FAT_SENSOR): sensor.sensor_schema(
            accuracy_decimals=1,
            state_class=STATE_CLASS_MEASUREMENT,
            icon="mdi:stomach",
        ),
        cv.Optional(CONF_ACTIVE_SENSOR): binary_sensor.binary_sensor_schema(
            device_class="running",
            icon="mdi:scale-bathroom",
        ),
        cv.Optional(CONF_LAST_READING_SENSOR): text_sensor.text_sensor_schema(
            icon="mdi:clock-outline",
        ),
    }
).extend(cv.COMPONENT_SCHEMA)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await ble_client.register_ble_node(var, config)

    cg.add(var.set_min_weight(config[CONF_MIN_WEIGHT]))
    cg.add(var.set_height(config[CONF_HEIGHT]))
    cg.add(var.set_age(config[CONF_AGE]))
    cg.add(var.set_gender_male(config[CONF_GENDER] == "male"))

    sensor_map = {
        CONF_WEIGHT_SENSOR: "set_weight_sensor",
        CONF_WEIGHT_LBS_SENSOR: "set_weight_lbs_sensor",
        CONF_IMPEDANCE_SENSOR: "set_impedance_sensor",
        CONF_BMI_SENSOR: "set_bmi_sensor",
        CONF_BODY_FAT_SENSOR: "set_body_fat_sensor",
        CONF_MUSCLE_MASS_SENSOR: "set_muscle_mass_sensor",
        CONF_WATER_PCT_SENSOR: "set_water_pct_sensor",
        CONF_BONE_MASS_SENSOR: "set_bone_mass_sensor",
        CONF_BMR_SENSOR: "set_bmr_sensor",
        CONF_VISCERAL_FAT_SENSOR: "set_visceral_fat_sensor",
    }

    for conf_key, setter in sensor_map.items():
        if conf_key in config:
            sens = await sensor.new_sensor(config[conf_key])
            cg.add(getattr(var, setter)(sens))

    if CONF_ACTIVE_SENSOR in config:
        sens = await binary_sensor.new_binary_sensor(config[CONF_ACTIVE_SENSOR])
        cg.add(var.set_active_sensor(sens))

    if CONF_LAST_READING_SENSOR in config:
        sens = await text_sensor.new_text_sensor(config[CONF_LAST_READING_SENSOR])
        cg.add(var.set_last_reading_sensor(sens))
