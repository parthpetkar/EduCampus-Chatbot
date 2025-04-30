<template>
  <div>
    <!-- Chatbot Toggle Button when chatbot is closed -->
    <button v-if="!isChatbotOpen" class="chatbot-toggle-btn" @click="toggleChatbot">
      <i class="fas fa-comments"></i>
    </button>

    <!-- Chatbot Panel -->
    <transition name="slide">
      <div v-if="isChatbotOpen" :class="['chatbot-container', { expanded: isExpanded }]" @mousedown="startDrag"
        @mousemove="onDrag" @mouseup="stopDrag" @mouseleave="stopDrag"
        :style="{ top: `${position.y}px`, left: `${position.x}px` }">
        <!-- Header Section -->
        <div class="chatbot-header">
          <img src="@/assets/image1.png" alt="Institution Logo" class="logo" />
          <h3 class="chatbot-title">Institute Support</h3>
          <button class="expand-chatbot-btn" @click="toggleExpand">
            <i :class="isExpanded ? 'fas fa-compress' : 'fas fa-expand'"></i>
          </button>
          <button @click="toggleNarration" class="toggle-narration-btn">
            <i :class="isNarrationEnabled ? 'fas fa-volume-up' : 'fas fa-volume-mute'"></i>
          </button>

          <button class="close-chatbot-btn" @click="toggleChatbot">
            <i class="fas fa-times"></i>
          </button>
        </div>

        <!-- Chat Window Section -->
        <div class="chatbot-window" ref="chatWindow">
          <div v-for="(message, index) in messages" :key="index" :class="messageClass(message.type)">
            <div class="message" v-html="message.text"></div>
          </div>
        </div>

        <!-- Input Area Section -->
        <div class="chatbot-input-area">
          <!-- File Upload -->
          <div class="file-upload-wrapper">
            <label class="file-upload-icon">
              <input type="file" name="file" @change="handleFileUpload" hidden />
              <i class="fas fa-paperclip"></i>
            </label>
            <span v-if="fileName" class="file-name-preview">
              {{ fileName }}
              <button class="delete-file-btn" @click="deleteFile">
                <i class="fas fa-times-circle"></i>
              </button>
            </span>
          </div>

          <!-- Microphone Button -->
          <button @click="toggleRecording" class="mic-btn">
            <i :class="isRecording ? 'fas fa-microphone-slash' : 'fas fa-microphone'"></i>
          </button>

          <!-- Text Input -->
          <input type="text" v-model="userInput" @keydown.enter="sendMessage" placeholder="Type your question here..."
            class="input-field" />

          <!-- Send Button -->
          <button @click="sendMessage" class="send-btn">
            <i class="fas fa-paper-plane"></i>
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>
<script>
import axios from "axios";
import DOMPurify from "dompurify";
import { marked } from "marked";

export default {
  data() {
    return {
      isChatbotOpen: false,
      isExpanded: false,
      userInput: "",
      file: null,
      fileName: null,
      messages: [
        { text: "Welcome to Institute Support! How can I assist you?", type: "bot" },
      ],
      position: { x: 20, y: 20 }, // Initial draggable position
      dragging: false,
      dragStart: { x: 0, y: 0 },
      isRecording: false, // Track recording state
      recognition: null, // Speech recognition instance
      audioChunks: [], // Store audio chunks
      isNarrationEnabled: true, // Default narration state
    };
  },

  methods: {
    toggleChatbot() {
      this.isChatbotOpen = !this.isChatbotOpen;
    },

    toggleExpand() {
      this.isExpanded = !this.isExpanded;
    },

    startDrag(event) {
      this.dragging = true;
      this.dragStart = {
        x: event.clientX - this.position.x,
        y: event.clientY - this.position.y,
      };
    },

    onDrag(event) {
      if (this.dragging) {
        this.position.x = event.clientX - this.dragStart.x;
        this.position.y = event.clientY - this.dragStart.y;
      }
    },

    stopDrag() {
      this.dragging = false;
    },

    handleFileUpload(event) {
      const uploadedFile = event.target.files[0];
      if (uploadedFile) {
        this.file = uploadedFile;
        this.fileName = uploadedFile.name;
      }
    },

    deleteFile() {
      this.file = null;
      this.fileName = null;
    },

    toggleRecording() {
      if (this.isRecording) {
        if (this.recognition) {
          this.recognition.stop();
        }
        this.isRecording = false;
      } else {
        this.startVoiceRecognition();
        this.isRecording = true;
      }
    },



    async startVoiceRecognition() {
      if (!("SpeechRecognition" in window || "webkitSpeechRecognition" in window)) {
        alert("Voice recognition is not supported in your browser.");
        return;
      }

      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      this.recognition = new SpeechRecognition();
      this.recognition.lang = "en-US";
      this.recognition.interimResults = false;

      this.recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        this.userInput += transcript; // Add transcribed text to userInput
      };

      this.recognition.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
      };

      this.recognition.onend = () => {
        this.isRecording = false;
      };

      this.recognition.start();
    },

    async sendMessage() {
      if (this.userInput.trim() !== "" || this.file) {
        const formData = new FormData();
        formData.append("query", this.userInput.trim());
        if (this.file) formData.append("file", this.file);

        this.messages.push({ text: this.userInput, type: "user" });
        this.userInput = "";

        try {
          const response = await axios.post("http://localhost:5000/api/query", formData, {
            headers: { "Content-Type": "multipart/form-data" },
          });
          console.log(response)
          const botResponse = this.formatBotResponse(response.data.response);
          this.messages.push({ text: botResponse, type: "bot" });
          if (this.isNarrationEnabled) {
            this.narrateText(botResponse);
          }

        } catch (error) {
          console.error("Error sending message:", error);
          const errorMessage = "Sorry, an error occurred.";
          this.messages.push({ text: errorMessage, type: "bot" });

          // Narrate the error message
          this.narrateText(errorMessage);
        }
      }
    },

    toggleNarration() {
      this.isNarrationEnabled = !this.isNarrationEnabled;

      // Stop any ongoing narration immediately
      if (!this.isNarrationEnabled) {
        window.speechSynthesis.cancel();
      }
    },


    messageClass(type) {
      return type === "user" ? "user-message" : "bot-message";
    },

    formatBotResponse(botResponse) {
      const pattern = /"response":\s*"(.*?)"/s;
      const match = pattern.exec(botResponse);
      let formattedText = match ? match[1] : botResponse;

      // Decode and clean up escaped characters
      formattedText = formattedText
        .replace(/\\n/g, "\n")
        .replace(/\\"/g, '"')
        .replace(/^Details:\s*/, "");

      // Convert URLs to buttons
      formattedText = formattedText.replace(/\b(?:https?|ftp):\/\/[^\s/$.?#].[^\s]*\b/g, (url) => {
        const buttonLabel = "Open Link";
        return `<button class="url-button" onclick="window.open('${url}', '_blank')">${buttonLabel}</button>`;
      });

      // Highlight emails
      formattedText = formattedText.replace(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, (email) => {
        return `<span class="highlight">${email}</span>`;
      });

      // Format phone numbers with icon
      formattedText = formattedText.replace(/\b\d{10}\b/g, (phone) => {
        return `<div class="contact">
          <span class="contact-icon">📞</span>
          <span class="contact-number">${phone}</span>
        </div>`;
      });

      // Convert Markdown to HTML and sanitize
      const html = marked.parse(formattedText);
      return DOMPurify.sanitize(html);
    },


    narrateText(text) {
      if (!("speechSynthesis" in window)) {
        console.warn("Speech synthesis not supported in this browser.");
        return;
      }

      // Cancel any ongoing narration
      window.speechSynthesis.cancel();

      if (this.isNarrationEnabled) {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = "en-US"; // Set language
        utterance.rate = 1;       // Adjust speed (1 is normal speed)
        utterance.pitch = 1;      // Adjust pitch (1 is normal pitch)

        window.speechSynthesis.speak(utterance);
      }
    },
  },
};
</script>
<style>
/* Draggable container */
.chatbot-container {
  position: absolute;
  width: 350px;
  height: 500px;
  background-color: #ffffff;
  border-radius: 12px;
  box-shadow: 0 6px 25px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  font-family: "Roboto", sans-serif;
  cursor: grab;
  z-index: 1200;
}

.chatbot-container:active {
  cursor: grabbing;
}

.expanded {
  width: 600px;
  height: 650px;
}

/* Toggle button styling */
.chatbot-toggle-btn {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background-color: #004f9e;
  color: white;
  border: none;
  padding: 15px;
  border-radius: 50%;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  cursor: pointer;
  z-index: 1100;
  transition: background-color 0.3s ease;
}

.chatbot-toggle-btn:hover {
  background-color: #003d7b;
}

/* Header styling */
.chatbot-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 15px;
  background-color: #004f9e;
  color: white;
}

.chatbot-header .logo {
  width: 35px;
  height: 35px;
  border-radius: 50%;
}

.chatbot-header .chatbot-title {
  flex: 1;
  font-size: 16px;
  margin-left: 10px;
  font-weight: bold;
  color: #ffffff;
}

.expand-chatbot-btn,
.close-chatbot-btn {
  background: none;
  border: none;
  color: white;
  font-size: 16px;
  cursor: pointer;
  margin-left: 5px;
}

.expand-chatbot-btn:hover,
.close-chatbot-btn:hover {
  color: #00b2ff;
}

/* Chat window styling */
.chatbot-window {
  flex: 1;
  padding: 10px;
  overflow-y: auto;
  background-color: #f4f7f9;
}

.message {
  padding: 8px 12px;
  border-radius: 12px;
  margin-bottom: 10px;
  max-width: 80%;
  word-wrap: break-word;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.bot-message {
  background-color: #ebf9ff;
  color: #333;
  align-self: flex-start;
  text-align: left;
  /* Ensures text is left-aligned */
}

.user-message {
  background-color: #cce5ff;
  color: #333;
  align-self: flex-end;
  text-align: right;
  /* Ensures text is left-aligned */
}

/* Input area styling */
.chatbot-input-area {
  display: flex;
  align-items: center;
  padding: 10px;
  border-top: 1px solid #ddd;
  background-color: #ffffff;
}

.input-field {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 20px;
  margin-right: 10px;
  font-size: 14px;
}

.send-btn {
  background-color: #004f9e;
  border: none;
  padding: 10px;
  border-radius: 50%;
  color: white;
  cursor: pointer;
  font-size: 16px;
}

.send-btn:hover {
  background-color: #003d7b;
}

/* File Upload */
.file-upload-wrapper {
  display: flex;
  align-items: center;
  margin-right: 10px;
}

.file-upload-icon {
  font-size: 20px;
  color: #004f9e;
  cursor: pointer;
}

.file-name-preview {
  font-size: 12px;
  margin-left: 10px;
  color: #888;
}

.delete-file-btn {
  background: none;
  border: none;
  color: #ff5c5c;
  cursor: pointer;
  margin-left: 5px;
}

.delete-file-btn:hover {
  color: #d93838;
}

/* Audio button styling */
.audio-btn-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: 10px;
  background-color: white;
}

.mic-btn {
  background-color: #004f9e;
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  cursor: pointer;
  font-size: 20px;
  transition: background-color 0.3s ease, transform 0.3s ease;
}

.audio-btn:hover {
  background-color: #003d7b;
  transform: scale(1.1);
}

.audio-btn:active {
  transform: scale(0.95);
  color: #003d7b;
}

.audio-btn i {
  pointer-events: none;
  /* Prevent the icon from triggering click events */
}

.audio-btn-recording {
  background-color: #ff5c5c;
}

.audio-btn-recording:hover {
  background-color: #d93838;
}

.audio-btn-recording:active {
  transform: scale(1);
}

/* Optional: Add a small label to explain the button */
.audio-btn-label {
  font-size: 12px;
  color: white;
  margin-top: 5px;
  display: none;
  /* You can toggle this label when needed */
}

.audio-btn-wrapper:hover .audio-btn-label {
  display: block;
}

/* Additions to the existing CSS */

.toggle-narration-btn {
  background: transparent;
  border: none;
  color: #ffffff;
  cursor: pointer;
  font-size: 18px;
  margin-left: 8px;
}

.toggle-narration-btn:hover {
  color: #ffffff;
}

/* Transparent button for URLs */
.url-button {
  background: transparent;
  border: none;
  color: blue;
  text-decoration: underline;
  cursor: pointer;
  padding: 0;
  font-size: inherit;
}

.url-button:hover {
  text-decoration: none;
}

.contact {
  display: flex;
  align-items: center;
  margin: 5px 0;
}

.contact-icon {
  margin-right: 8px;
  color: #e63946;
  /* Red color for phone icon */
}

.contact-number {
  font-size: 14px;
  color: #333;
}


/* Icons for email and phone */
.email-icon::before {
  content: "📧";
}

.phone-icon::before {
  content: "📞";
}

/* List styling */
ul {
  margin: 10px 0;
  padding-left: 20px;
}

li {
  margin: 5px 0;
}
</style>
