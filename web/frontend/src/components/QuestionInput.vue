<template>
  <div class="question-input">
    <label :for="question.id" class="label">
      {{ question.label }}
      <span v-if="!question.required && !question.conditional" class="optional">(optional)</span>
    </label>

    <!-- Number input -->
    <template v-if="question.type === 'number'">
      <div class="input-group">
        <input
          :id="question.id"
          type="number"
          :value="value"
          :min="question.min"
          :max="question.max"
          :placeholder="question.default"
          @input="handleInput"
          class="input"
        />
        <span v-if="question.unit" class="unit">{{ question.unit }}</span>
      </div>
    </template>

    <!-- Text input -->
    <template v-else-if="question.type === 'text'">
      <input
        :id="question.id"
        type="text"
        :value="value || ''"
        :placeholder="question.placeholder"
        @input="handleInput"
        class="input"
      />
    </template>

    <!-- Boolean / toggle -->
    <template v-else-if="question.type === 'boolean'">
      <div class="toggle-group">
        <button
          class="toggle-btn"
          :class="{ active: value === true }"
          @click="() => $emit('update', true)"
          type="button"
        >
          Yes
        </button>
        <button
          class="toggle-btn"
          :class="{ active: value === false || value === null }"
          @click="() => $emit('update', false)"
          type="button"
        >
          No
        </button>
      </div>
    </template>

    <!-- Help text -->
    <div v-if="question.help" class="help-text">
      💡 {{ question.help }}
    </div>
  </div>
</template>

<script>
export default {
  name: 'QuestionInput',
  props: {
    question: {
      type: Object,
      required: true
    },
    value: {
      type: [String, Number, Boolean, null],
      default: null
    }
  },
  emits: ['update'],
  setup(props, { emit }) {
    const handleInput = (e) => {
      const value = e.target.value
      if (props.question.type === 'number') {
        emit('update', value ? parseFloat(value) : null)
      } else {
        emit('update', value)
      }
    }

    return { handleInput }
  }
}
</script>

<style scoped>
.question-input {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.label {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
}

.optional {
  font-weight: 400;
  color: #9ca3af;
  font-size: 12px;
}

.input-group {
  position: relative;
  display: flex;
  align-items: center;
}

.input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.unit {
  position: absolute;
  right: 12px;
  color: #9ca3af;
  font-size: 13px;
  pointer-events: none;
}

.toggle-group {
  display: flex;
  gap: 8px;
}

.toggle-btn {
  flex: 1;
  padding: 10px 16px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  color: #6b7280;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-btn:hover {
  border-color: #3b82f6;
  color: #3b82f6;
}

.toggle-btn.active {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.help-text {
  font-size: 12px;
  color: #6b7280;
  line-height: 1.4;
}
</style>
