"""Domestic event catalog: actual HA state machine, no live HA or device calls."""
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from homeassistant.core import HomeAssistant
import custom_components.ha2_notifications as integration
from test_engine import MemoryStore

ROOT = Path(__file__).resolve().parents[2]

class EntityCatalogTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.hass = HomeAssistant(str(ROOT / 'test-catalog-config'))
        self.hass.config.time_zone = 'Atlantic/Canary'
        entry = SimpleNamespace(data={'target_prefix':'xiaozhi_ball_v2','weather_entity':'weather.forecast_casa'})
        with patch.object(integration, 'Store', return_value=MemoryStore()):
            self.runtime = integration.Runtime(self.hass, entry)

    async def test_vacuum_catalog_exposes_canonical_states_and_accepts_its_transition(self):
        self.hass.states.async_set('vacuum.robot_test', 'returning', {'friendly_name':'Robot de prueba'})
        options = self.runtime.entity_options()
        self.assertIn('vacuum.robot_test', [item['entity_id'] for item in options])
        item = next(item for item in options if item['entity_id'] == 'vacuum.robot_test')
        self.assertEqual(item['name'], 'Robot de prueba')
        self.assertEqual(item['state'], 'returning')
        self.assertIn('docked', item['state_options'])
        self.assertEqual(item['state_options_source'], 'domain')
        rid = await self.runtime.engine.command('save', expected_revision=0, rule={
            'name':'Regreso a base', 'title':'Robot', 'body':'Ha vuelto a la base.',
            'trigger':'state', 'enabled':True, 'entity_id':'vacuum.robot_test', 'to_state':'docked'})
        await self.runtime.engine.state_changed('vacuum.robot_test', 'returning', 'docked')
        self.assertEqual([q['rule_id'] for q in self.runtime.engine.data['queue']], [rid])
        self.assertNotIn('vacuum.inventada', [item['entity_id'] for item in self.runtime.entity_options()])

    async def test_entity_suggestions_use_declared_values_domains_or_current_state(self):
        self.hass.states.async_set('binary_sensor.door_test', 'off')
        self.hass.states.async_set('select.program_test', 'Eco', {'options':['Eco','Turbo']})
        self.hass.states.async_set('climate.room_test', 'cool', {'hvac_modes':['off','cool']})
        self.hass.states.async_set('sensor.temperature_test', '23.5', {'unit_of_measurement':'°C'})
        self.hass.states.async_set('light.lamp_test', 'on')
        self.hass.states.async_set('number.level_test', '3')
        self.hass.states.async_set('conversation.not_a_device', 'ready')
        catalog={item['entity_id']:item for item in self.runtime.entity_options()}
        self.assertEqual(catalog['binary_sensor.door_test']['state_options'], ['off','on'])
        self.assertEqual(catalog['select.program_test']['state_options'], ['Eco','Turbo'])
        self.assertEqual(catalog['select.program_test']['state_options_source'], 'declared')
        self.assertEqual(catalog['climate.room_test']['state_options'], ['off','cool'])
        self.assertEqual(catalog['sensor.temperature_test']['state_options'], ['23.5'])
        self.assertEqual(catalog['sensor.temperature_test']['state_options_source'], 'current')
        self.assertEqual(catalog['light.lamp_test']['state_options'], ['off','on'])
        self.assertIn('number.level_test',catalog)
        self.assertNotIn('conversation.not_a_device',catalog)
        self.assertEqual([item['entity_id'] for item in self.runtime.entity_options()],sorted(catalog))

    async def test_suggestion_payload_is_bounded_and_does_not_copy_other_attributes(self):
        self.hass.states.async_set('select.long_test', 'valid', {'options':['unknown','unavailable',None,1,'',' ','x'*256,'valid','valid']+[str(x) for x in range(100)],'private_attribute':'do-not-copy'})
        item=self.runtime.entity_options()[0]
        self.assertLessEqual(len(item['state_options']),64)
        self.assertEqual(len(item['state_options']),len(set(item['state_options'])))
        self.assertTrue(all(isinstance(x,str) and x.strip() and len(x)<=255 and x not in ('unknown','unavailable') for x in item['state_options']))
        self.assertEqual(set(item),{'entity_id','name','state','state_options','state_options_source'})
        self.assertNotIn('do-not-copy',str(item))
