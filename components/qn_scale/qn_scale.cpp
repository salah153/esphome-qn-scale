#include "qn_scale.h"
#include "esphome/core/log.h"
#include <ctime>

namespace esphome {
namespace qn_scale {

static const char *const TAG = "qn_scale";

void QNScale::dump_config() {
  ESP_LOGCONFIG(TAG, "QN Scale:");
  ESP_LOGCONFIG(TAG, "  Min Weight: %.1f kg", min_weight_);
}

void QNScale::loop() {
  if (reading_active_ && (millis() - last_reading_time_ > 60000)) {
    reading_active_ = false;
    if (active_sensor_)
      active_sensor_->publish_state(false);
    this->parent()->disconnect();  // Timeout: release scale so it can sleep
  }
}

uint8_t QNScale::checksum_(const uint8_t *data, uint16_t length) {
  uint8_t sum = 0;
  for (uint16_t i = 0; i < length; i++)
    sum += data[i];
  return sum & 0xFF;
}

void QNScale::write_characteristic_(uint16_t uuid, const uint8_t *data, uint16_t length) {
  uint16_t handle = 0;
  if (uuid == CHR_CFG_UUID)
    handle = cfg_handle_;
  else if (uuid == CHR_TIME_UUID)
    handle = time_handle_;

  if (handle == 0) {
    ESP_LOGW(TAG, "Cannot write: handle for UUID 0x%04X not found", uuid);
    return;
  }

  auto status = esp_ble_gattc_write_char(this->parent()->get_gattc_if(),
                                          this->parent()->get_conn_id(), handle,
                                          length, const_cast<uint8_t *>(data),
                                          ESP_GATT_WRITE_TYPE_RSP,
                                          ESP_GATT_AUTH_REQ_NONE);
  if (status) {
    ESP_LOGW(TAG, "Write to 0x%04X failed: %d", uuid, status);
  }
}

void QNScale::send_config_() {
  if (config_sent_)
    return;
  config_sent_ = true;

  uint8_t cfg[] = {0x13, 0x09, protocol_type_, 0x01, 0x10, 0x00, 0x00, 0x00, 0x00};
  cfg[8] = checksum_(cfg, 8);
  write_characteristic_(CHR_CFG_UUID, cfg, sizeof(cfg));

  uint32_t ts = (uint32_t)(time(nullptr)) - QN_EPOCH;
  uint8_t time_msg[5];
  time_msg[0] = 0x02;
  time_msg[1] = ts & 0xFF;
  time_msg[2] = (ts >> 8) & 0xFF;
  time_msg[3] = (ts >> 16) & 0xFF;
  time_msg[4] = (ts >> 24) & 0xFF;
  write_characteristic_(CHR_TIME_UUID, time_msg, sizeof(time_msg));

  ESP_LOGI(TAG, "Config + time sync sent");
}

void QNScale::send_time_ack_() {
  uint32_t ts = (uint32_t)(time(nullptr)) - QN_EPOCH;
  uint8_t msg[] = {0x20, 0x08, protocol_type_,
                   (uint8_t)(ts & 0xFF), (uint8_t)((ts >> 8) & 0xFF),
                   (uint8_t)((ts >> 16) & 0xFF), (uint8_t)((ts >> 24) & 0xFF),
                   0x00};
  msg[7] = checksum_(msg, 7);
  write_characteristic_(CHR_CFG_UUID, msg, sizeof(msg));
}

void QNScale::send_stored_data_response_() {
  uint8_t msg1[] = {0xA0, 0x0D, 0x04, 0xFE, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00};
  msg1[12] = checksum_(msg1, 12);

  uint8_t msg2[] = {0xA0, 0x0D, 0x02, 0x01, 0x00, 0x08, 0x00, 0x21,
                    0x06, 0xB8, 0x04, 0x02, 0x00};
  msg2[12] = checksum_(msg2, 12);

  uint8_t q22[] = {0x22, 0x06, protocol_type_, 0x00, 0x03, 0x00};
  q22[5] = checksum_(q22, 5);

  write_characteristic_(CHR_CFG_UUID, msg1, sizeof(msg1));
  write_characteristic_(CHR_CFG_UUID, msg2, sizeof(msg2));
  write_characteristic_(CHR_CFG_UUID, q22, sizeof(q22));
}

void QNScale::handle_notification_(uint16_t handle, const uint8_t *data, uint16_t length) {
  if (length < 3)
    return;

  uint8_t opcode = data[0];

  if (protocol_type_ == 0x00)
    protocol_type_ = data[2];

  if (opcode == 0x12) {
    if (length > 10 && data[10] == 0x01)
      scale_factor_ = 100.0f;
    else
      scale_factor_ = 10.0f;

    char hex[length * 3 + 1];
    for (uint16_t i = 0; i < length; i++)
      sprintf(hex + i * 3, "%02X ", data[i]);
    hex[length * 3] = '\0';
    ESP_LOGI(TAG, "Scale info raw (%u bytes): %s", length, hex);
    ESP_LOGI(TAG, "Scale info received (factor: %.0f)", scale_factor_);
    send_config_();

  } else if (opcode == 0x10) {
    uint8_t byte4 = data[4];
    bool is_es30m = byte4 <= 0x02 && scale_factor_ == 10.0f;
    bool stable;
    uint16_t raw;
    uint16_t r1 = 0, r2 = 0;

    if (is_es30m) {
      if (length < 11) return;
      stable = (byte4 == 0x01 || byte4 == 0x02);
      raw = ((uint16_t)data[5] << 8) | data[6];
      if (length >= 11) {
        r1 = ((uint16_t)data[7] << 8) | data[8];
        r2 = ((uint16_t)data[9] << 8) | data[10];
      }
    } else {
      if (length < 10) return;
      stable = (data[5] == 0x01);
      raw = ((uint16_t)data[3] << 8) | data[4];
      if (length >= 10) {
        r1 = ((uint16_t)data[6] << 8) | data[7];
        r2 = ((uint16_t)data[8] << 8) | data[9];
      }
    }

    float weight = raw / scale_factor_;
    if (weight >= 250.0f)
      weight /= 10.0f;

    if (!reading_active_) {
      reading_active_ = true;
      if (active_sensor_)
        active_sensor_->publish_state(true);
    }
    last_reading_time_ = millis();

    if (stable && weight >= min_weight_) {
      ESP_LOGI(TAG, "Stable: %.2f kg, R1=%u, R2=%u", weight, r1, r2);

      if (weight_sensor_)
        weight_sensor_->publish_state(weight);
      if (impedance_r1_sensor_)
        impedance_r1_sensor_->publish_state((float)r1);
      if (impedance_r2_sensor_)
        impedance_r2_sensor_->publish_state((float)r2);

      reading_active_ = false;
      if (active_sensor_)
        active_sensor_->publish_state(false);
      this->parent()->disconnect();  // Release scale so it can sleep

    } else if (!stable) {
      ESP_LOGD(TAG, "Measuring: %.2f kg (R1=%u R2=%u)", weight, r1, r2);
    }

  } else if (opcode == 0x14) {
    send_time_ack_();

  } else if (opcode == 0x21) {
    send_stored_data_response_();
  } else {
    // Unknown opcode — dump raw bytes for reverse engineering
    char hex[length * 3 + 1];
    for (uint16_t i = 0; i < length; i++)
      sprintf(hex + i * 3, "%02X ", data[i]);
    hex[length * 3] = '\0';
    ESP_LOGI(TAG, "Unknown opcode 0x%02X (%u bytes): %s", opcode, length, hex);
  }
}

void QNScale::gattc_event_handler(esp_gattc_cb_event_t event,
                                   esp_gatt_if_t gattc_if,
                                   esp_ble_gattc_cb_param_t *param) {
  switch (event) {
    case ESP_GATTC_DISCONNECT_EVT: {
      ESP_LOGI(TAG, "Scale disconnected");
      config_sent_ = false;
      protocol_type_ = 0x00;
      notify_handle_ = 0;
      misc_handle_ = 0;
      cfg_handle_ = 0;
      time_handle_ = 0;
      reading_active_ = false;
      if (active_sensor_)
        active_sensor_->publish_state(false);
      break;
    }

    case ESP_GATTC_SEARCH_CMPL_EVT: {
      auto *chr_notify = this->parent()->get_characteristic(0xFFE0, CHR_NOTIFY_UUID);
      auto *chr_misc = this->parent()->get_characteristic(0xFFE0, CHR_MISC_UUID);
      auto *chr_cfg = this->parent()->get_characteristic(0xFFE0, CHR_CFG_UUID);
      auto *chr_time = this->parent()->get_characteristic(0xFFE0, CHR_TIME_UUID);

      if (chr_notify == nullptr) {
        ESP_LOGW(TAG, "FFE1 (notify) characteristic not found");
        break;
      }

      notify_handle_ = chr_notify->handle;
      if (chr_misc) misc_handle_ = chr_misc->handle;
      if (chr_cfg) cfg_handle_ = chr_cfg->handle;
      if (chr_time) time_handle_ = chr_time->handle;

      ESP_LOGI(TAG, "Handles: notify=0x%04X misc=0x%04X cfg=0x%04X time=0x%04X",
               notify_handle_, misc_handle_, cfg_handle_, time_handle_);

      auto status = esp_ble_gattc_register_for_notify(
          gattc_if, this->parent()->get_remote_bda(), notify_handle_);
      if (status) {
        ESP_LOGW(TAG, "Register notify failed: %d", status);
      }

      if (misc_handle_) {
        esp_ble_gattc_register_for_notify(
            gattc_if, this->parent()->get_remote_bda(), misc_handle_);
      }
      break;
    }

    case ESP_GATTC_NOTIFY_EVT: {
      if (param->notify.handle == notify_handle_) {
        handle_notification_(param->notify.handle, param->notify.value,
                           param->notify.value_len);
      }
      break;
    }

    default:
      break;
  }
}

}  // namespace qn_scale
}  // namespace esphome
