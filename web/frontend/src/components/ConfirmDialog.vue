<template>
  <div class="dialog-overlay" @click.self="$emit('cancel')">
    <div class="dialog-box" :class="{ danger }">
      <h2>{{ title }}</h2>
      <p>{{ message }}</p>
      <div class="dialog-buttons">
        <button @click="$emit('cancel')" class="btn-cancel">
          {{ cancelText }}
        </button>
        <button @click="$emit('confirm')" class="btn-confirm" :class="{ danger }">
          {{ confirmText }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true
  },
  message: {
    type: String,
    required: true
  },
  confirmText: {
    type: String,
    default: 'Confirm'
  },
  cancelText: {
    type: String,
    default: 'Cancel'
  },
  danger: {
    type: Boolean,
    default: false
  }
})

defineEmits(['confirm', 'cancel'])
</script>

<style scoped>
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog-box {
  background-color: #fff;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  max-width: 400px;
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

.dialog-box h2 {
  margin: 0 0 12px 0;
  font-size: 18px;
  color: #333;
}

.dialog-box.danger h2 {
  color: #d32f2f;
}

.dialog-box p {
  margin: 0 0 24px 0;
  font-size: 14px;
  color: #666;
  line-height: 1.5;
}

.dialog-buttons {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.btn-cancel, .btn-confirm {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
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

.btn-confirm {
  background-color: #667eea;
  color: white;
}

.btn-confirm:hover {
  background-color: #5568d3;
}

.btn-confirm.danger {
  background-color: #d32f2f;
}

.btn-confirm.danger:hover {
  background-color: #b71c1c;
}
</style>
