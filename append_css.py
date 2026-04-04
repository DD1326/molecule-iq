with open('static/css/style.css', 'a', encoding='utf-8') as f:
    f.write('''
/* ============================================================
   CHATBOT WIDGET STYLES
   ============================================================ */
.chatbot-widget {
  position: fixed;
  bottom: 30px;
  right: 30px;
  z-index: 9999;
  font-family: var(--font-body);
}

.chatbot-toggle-btn {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: var(--bg-card);
  border: 1px solid var(--accent);
  color: var(--accent);
  box-shadow: 0 4px 15px rgba(0, 229, 160, 0.2);
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 1.8rem;
  transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
.chatbot-toggle-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 20px rgba(0, 229, 160, 0.4);
}

.chatbot-window {
  position: absolute;
  bottom: 80px;
  right: 0;
  width: 350px;
  height: 500px;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: 15px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 10px 40px rgba(0,0,0,0.5);
  transition: opacity 0.3s ease, transform 0.3s ease;
  transform-origin: bottom right;
}

.chatbot-window.hidden {
  opacity: 0;
  transform: scale(0);
  pointer-events: none;
}

.chatbot-header {
  padding: 15px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.chatbot-title {
  font-weight: 600;
  color: var(--accent);
}
.chatbot-close-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 1.2rem;
}
.chatbot-close-btn:hover {
  color: #ff5e8a;
}

.chatbot-messages {
  flex: 1;
  padding: 15px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.chatbot-message {
  padding: 10px 15px;
  border-radius: 12px;
  max-width: 85%;
  line-height: 1.4;
  font-size: 0.95rem;
}

.bot-message {
  background: var(--bg-card);
  color: var(--text-main);
  align-self: flex-start;
  border: 1px solid var(--border);
}
.bot-message p {
  margin: 0 0 10px 0;
}
.bot-message p:last-child {
  margin-bottom: 0;
}

.user-message {
  background: rgba(0, 229, 160, 0.1);
  color: var(--accent);
  align-self: flex-end;
  border: 1px solid rgba(0, 229, 160, 0.3);
}

.chatbot-input-area {
  display: flex;
  padding: 15px;
  background: var(--bg-card);
  border-top: 1px solid var(--border);
}

.chatbot-input {
  flex: 1;
  background: var(--bg-main);
  border: 1px solid var(--border);
  padding: 10px;
  border-radius: 8px;
  color: var(--text-main);
}
.chatbot-input:focus {
  outline: none;
  border-color: var(--accent);
}
.chatbot-send-btn {
  background: var(--accent);
  color: #000;
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  margin-left: 10px;
  cursor: pointer;
  font-size: 1.2rem;
}
.chatbot-send-btn:hover {
  opacity: 0.9;
}
''')
