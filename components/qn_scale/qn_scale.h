#pragma once

#include "esphome/core/component.h"
#include "esphome/components/ble_client/ble_client.h"
#include "esphome/components/sensor/sensor.h"
#include "esphome/components/text_sensor/text_sensor.h"
#include "esphome/components/binary_sensor/binary_sensor.h"

namespace esphome {
namespace qn_scale {

// QN-Scale BLE Protocol UUIDs (service 0xFFE0)
static const uint16_t CHR_NOTIFY_UUID = 0xFFE1;
static const uint16_t CHR_MISC_UUID = 0xFFE2;
static const uint16_t CHR_CFG_UUID = 0xFFE3;
static const uint16_t CHR_TIME_UUID = 0xFFE4;

// Custom epoch: 2000-01-01 00:00:00 UTC
static const uint32_t QN_EPOCH = 946702800;

class QNScale : public ble_client::BLEClientNode, public Component {
 public:
  void setup() override {}
  void loop() override;
  void dump_config() override;
  float get_setup_priority() const override { return setup_priority::DATA; }

  void gattc_event_handler(esp_gattc_cb_event_t event, esp_gatt_if_t gattc_if,
                           esp_ble_gattc_cb_param_t *param) override;

  void set_weight_sensor(sensor::Sensor *sensor) { weight_sensor_ = sensor; }
  void set_weight_lbs_sensor(sensor::Sensor *sensor) { weight_lbs_sensor_ = sensor; }
  void set_active_sensor(binary_sensor::BinarySensor *sensor) { active_sensor_ = sensor; }
  void set_last_reading_sensor(text_sensor::TextSensor *sensor) { last_reading_sensor_ = sensor; }
  void set_min_weight(float min_weight) { min_weight_ = min_weight; }

 protected:
  void handle_notification_(uint16_t handle, const uint8_t *data, uint16_t length);
  void send_config_();
  void send_time_ack_();
  void send_stored_data_response_();
  void write_characteristic_(uint16_t uuid, const uint8_t *data, uint16_t length);
  uint8_t checksum_(const uint8_t *data, uint16_t length);

  sensor::Sensor *weight_sensor_{nullptr};
  sensor::Sensor *weight_lbs_sensor_{nullptr};
  binary_sensor::BinarySensor *active_sensor_{nullptr};
  text_sensor::TextSensor *last_reading_sensor_{nullptr};

  uint16_t notify_handle_{0};
  uint16_t misc_handle_{0};
  uint16_t cfg_handle_{0};
  uint16_t time_handle_{0};

  float scale_factor_{100.0f};
  uint8_t protocol_type_{0x00};
  bool config_sent_{false};
  bool reading_active_{false};
  float min_weight_{20.0f};

  uint32_t last_reading_time_{0};
};

}  // namespace qn_scale
}  // namespace esphome
