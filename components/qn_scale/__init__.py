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
CONF_WEIGHT_SENSOR = "weight_sensor"
CONF_WEIGHT_LBS_SENSOR = "weight_lbs_sensor"
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

    if CONF_WEIGHT_SENSOR in config:
        sens = await sensor.new_sensor(config[CONF_WEIGHT_SENSOR])
        cg.add(var.set_weight_sensor(sens))

    if CONF_WEIGHT_LBS_SENSOR in config:
        sens = await sensor.new_sensor(config[CONF_WEIGHT_LBS_SENSOR])
        cg.add(var.set_weight_lbs_sensor(sens))

    if CONF_ACTIVE_SENSOR in config:
        sens = await binary_sensor.new_binary_sensor(config[CONF_ACTIVE_SENSOR])
        cg.add(var.set_active_sensor(sens))

    if CONF_LAST_READING_SENSOR in config:
        sens = await text_sensor.new_text_sensor(config[CONF_LAST_READING_SENSOR])
        cg.add(var.set_last_reading_sensor(sens))
