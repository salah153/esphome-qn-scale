import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import ble_client, sensor, binary_sensor
from esphome.const import (
    CONF_ID,
    DEVICE_CLASS_WEIGHT,
    STATE_CLASS_MEASUREMENT,
    UNIT_KILOGRAM,
)

DEPENDENCIES = ["ble_client"]
AUTO_LOAD = ["sensor", "binary_sensor"]

CONF_BLE_CLIENT_ID = "ble_client_id"
CONF_MIN_WEIGHT = "min_weight"
CONF_WEIGHT_SENSOR = "weight_sensor"
CONF_IMPEDANCE_R1_SENSOR = "impedance_r1_sensor"
CONF_IMPEDANCE_R2_SENSOR = "impedance_r2_sensor"
CONF_ACTIVE_SENSOR = "active_sensor"

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
        cv.Optional(CONF_IMPEDANCE_R1_SENSOR): sensor.sensor_schema(
            unit_of_measurement="\u03A9",
            accuracy_decimals=0,
            state_class=STATE_CLASS_MEASUREMENT,
            icon="mdi:flash-triangle-outline",
        ),
        cv.Optional(CONF_IMPEDANCE_R2_SENSOR): sensor.sensor_schema(
            unit_of_measurement="\u03A9",
            accuracy_decimals=0,
            state_class=STATE_CLASS_MEASUREMENT,
            icon="mdi:flash-triangle-outline",
        ),
        cv.Optional(CONF_ACTIVE_SENSOR): binary_sensor.binary_sensor_schema(
            device_class="running",
            icon="mdi:scale-bathroom",
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

    if CONF_IMPEDANCE_R1_SENSOR in config:
        sens = await sensor.new_sensor(config[CONF_IMPEDANCE_R1_SENSOR])
        cg.add(var.set_impedance_r1_sensor(sens))

    if CONF_IMPEDANCE_R2_SENSOR in config:
        sens = await sensor.new_sensor(config[CONF_IMPEDANCE_R2_SENSOR])
        cg.add(var.set_impedance_r2_sensor(sens))

    if CONF_ACTIVE_SENSOR in config:
        sens = await binary_sensor.new_binary_sensor(config[CONF_ACTIVE_SENSOR])
        cg.add(var.set_active_sensor(sens))
