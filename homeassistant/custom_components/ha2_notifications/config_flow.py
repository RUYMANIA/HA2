"""Single-entry UI configuration, no secrets or device writes."""
import voluptuous as vol
from homeassistant import config_entries
from . import DOMAIN, Error, validate_target

class NotificationsConfigFlow(config_entries.ConfigFlow,domain=DOMAIN):
    VERSION=1
    async def async_step_user(self,user_input=None):
        if self._async_current_entries(): return self.async_abort(reason='single_instance_allowed')
        errors={}
        if user_input is not None:
            try:
                data=validate_target(self.hass,user_input)
                return self.async_create_entry(title='HA² Notifications',data=data)
            except Error: errors['base']='config_error'
        return self.async_show_form(step_id='user',data_schema=vol.Schema({
            vol.Required('target_prefix',default='xiaozhi_ball_v2'):str,
            vol.Required('weather_entity',default='weather.forecast_casa'):str}),errors=errors)
