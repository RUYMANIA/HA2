import unittest
from types import SimpleNamespace
from homeassistant.core import HomeAssistant,Context
from homeassistant.components import conversation
from custom_components.hermes_agent.conversation import HermesConversationEntity

class AdapterTests(unittest.IsolatedAsyncioTestCase):
 async def asyncSetUp(self):
  self.hass=HomeAssistant('/config/.ha2-development-tests/native-fixture');self.calls=[]
  async def infer(**kw):self.calls.append(kw);return SimpleNamespace(text='Respuesta de fixture')
  entry=SimpleNamespace(entry_id='fixture',title='Hermes',options={},runtime_data=SimpleNamespace(client=SimpleNamespace(async_inference=infer)))
  self.agent=HermesConversationEntity(entry);self.agent.hass=self.hass
 def make(self,native=True,prior=False):
  sid='01M5H0000000000000000000000';sat='assist_satellite.xiaozhi_ball_v2_assist_satellite';opener='¿Te apetece comentar algo?'
  log=conversation.ChatLog(self.hass,sid)
  if prior:log.async_add_user_content(conversation.UserContent(content='turno previo'))
  log.async_add_assistant_content_without_tools(conversation.AssistantContent(agent_id=sat if native else 'conversation.hermes',content=opener))
  log.async_add_user_content(conversation.UserContent(content='Sí, sobre dinosaurios'))
  user=conversation.ConversationInput(text='Sí, sobre dinosaurios',context=Context(),conversation_id=sid,device_id='shared-fixture',satellite_id=sat,language='es',agent_id='conversation.hermes',extra_system_prompt=opener)
  return user,log
 async def test_native_first_reply_carries_opener_as_user_context_not_system(self):
  user,log=self.make();result=await self.agent._async_handle_message(user,log);sent=self.calls[0]
  self.assertTrue(sent.get('bootstrap_session'))
  self.assertIn('¿Te apetece comentar algo?',sent['messages'][-1]['content']);self.assertIn('Sí, sobre dinosaurios',sent['messages'][-1]['content'])
  self.assertEqual(sent['messages'][-1]['role'],'user');self.assertNotIn('system_prompt',sent);self.assertEqual(result.conversation_id,user.conversation_id)
 async def test_manual_path_unchanged(self):
  user,log=self.make(native=False);await self.agent._async_handle_message(user,log)
  self.assertNotIn('bootstrap_session',self.calls[0]);self.assertEqual(self.calls[0]['messages'][-1]['content'],user.text)
 async def test_later_turn_does_not_bootstrap_or_duplicate_opener(self):
  user,log=self.make(prior=True);await self.agent._async_handle_message(user,log)
  self.assertNotIn('bootstrap_session',self.calls[0]);self.assertEqual(self.calls[0]['messages'][-1]['content'],user.text)
