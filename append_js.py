with open('static/js/main.js', 'a', encoding='utf-8') as f:
    f.write('''
// ============================================================
// CHATBOT WIDGET LOGIC
// ============================================================
const chatbotBtn = document.getElementById('chatbot-toggle-btn');
const chatbotWin = document.getElementById('chatbot-window');
const chatCloseBtn = document.getElementById('chatbot-close-btn');
const chatSendBtn = document.getElementById('chatbot-send-btn');
const chatInput = document.getElementById('chatbot-input');
const chatMessages = document.getElementById('chatbot-messages');

if (chatbotBtn && chatbotWin) {
  chatbotBtn.addEventListener('click', () => {
    chatbotWin.classList.toggle('hidden');
    if (!chatbotWin.classList.contains('hidden')) {
      chatInput.focus();
    }
  });
}

if (chatCloseBtn) {
  chatCloseBtn.addEventListener('click', () => {
    chatbotWin.classList.add('hidden');
  });
}

function appendMessage(text, type='bot') {
  const msgDiv = document.createElement('div');
  msgDiv.className = `chatbot-message ${type}-message`;
  if (type === 'bot') {
    if (typeof marked !== 'undefined') {
      msgDiv.innerHTML = marked.parse(text); 
    } else {
      msgDiv.textContent = text;
    }
  } else {
    msgDiv.textContent = text; 
  }
  chatMessages.appendChild(msgDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

if (chatSendBtn && chatInput) {
  const sendMessage = async () => {
    const text = chatInput.value.trim();
    if (!text) return;
    
    // Append user msg
    appendMessage(text, 'user');
    chatInput.value = '';
    
    // Show typing state
    const loadingId = 'loading-' + Date.now();
    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'chatbot-message bot-message';
    loadingMsg.id = loadingId;
    loadingMsg.innerHTML = '<span class="typing">...</span>';
    chatMessages.appendChild(loadingMsg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: text })
      });
      const data = await response.json();
      
      const loadElem = document.getElementById(loadingId);
      if (loadElem) loadElem.remove();
      
      if (data.error) {
        appendMessage('⚠️ Error: ' + data.error, 'bot');
      } else {
        appendMessage(data.agent_response || 'No response', 'bot');
      }
    } catch (err) {
      const loadElem = document.getElementById(loadingId);
      if (loadElem) loadElem.remove();
      appendMessage('⚠️ Network Error: ' + err.message, 'bot');
    }
  };
  
  chatSendBtn.addEventListener('click', sendMessage);
  chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  });
}
''')
