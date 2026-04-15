<template>
  <div class="modal-overlay" @click.self="$emit('cancel')">
    <div class="modal-box">
      <div class="modal-header">
        <h2>Save Scenario As</h2>
        <button @click="$emit('cancel')" class="btn-close">✕</button>
      </div>

      <div class="modal-body">
        <label for="scenario-name">Scenario Name</label>
        <input
          id="scenario-name"
          v-model="scenarioName"
          type="text"
          placeholder="Enter scenario name"
          @keyup.enter="handleSave"
          autofocus
        />
        <p class="helper-text">
          Name will help you identify this scenario later.
        </p>
      </div>

      <div class="modal-footer">
        <button @click="$emit('cancel')" class="btn-cancel">
          Cancel
        </button>
        <button @click="handleSave" class="btn-save" :disabled="!scenarioName.trim()">
          💾 Save
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  defaultName: {
    type: String,
    default: 'My Scenario'
  }
})

const emit = defineEmits(['save', 'cancel'])

const scenarioName = ref(props.defaultName)

// Update when defaultName prop changes
watch(() => props.defaultName, (newName) => {
  scenarioName.value = newName
})

const handleSave = () => {
  if (scenarioName.value.trim()) {
    emit('save', scenarioName.value.trim())
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1001;
}

.modal-box {
  background-color: #fff;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  max-width: 500px;
  width: 90%;
  animation: slideIn 0.2s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e0e0e0;
}

.modal-header h2 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.btn-close {
  padding: 4px 8px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 20px;
  color: #999;
  transition: color 0.2s;
}

.btn-close:hover {
  color: #333;
}

.modal-body {
  padding: 24px;
}

.modal-body label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #555;
  margin-bottom: 8px;
}

.modal-body input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
  box-sizing: border-box;
  transition: border-color 0.2s;
}

.modal-body input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.helper-text {
  margin: 8px 0 0 0;
  font-size: 12px;
  color: #999;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid #e0e0e0;
}

.btn-cancel, .btn-save {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel {
  background-color: #f0f0f0;
  color: #333;
}

.btn-cancel:hover {
  background-color: #e0e0e0;
}

.btn-save {
  background-color: #4caf50;
  color: white;
}

.btn-save:hover:not(:disabled) {
  background-color: #45a049;
}

.btn-save:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
