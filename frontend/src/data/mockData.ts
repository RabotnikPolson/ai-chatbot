import type { Chat, Message, User } from '../types';

// ─── Mock User ────────────────────────────────────────────────────────────────

export const mockUser: User = {
    id: 'user-1',
    email: 'damir@example.com',
    name: 'Damir',
};

// ─── Mock Chats ───────────────────────────────────────────────────────────────

export const mockChats: Chat[] = [
    {
        id: 'chat-1',
        title: 'Что такое нейронная',
        createdAt: '2026-03-04T08:00:00Z',
        updatedAt: '2026-03-04T08:15:00Z',
        hasNewActivity: false,
    },
    {
        id: 'chat-2',
        title: 'Напиши код на',
        createdAt: '2026-03-04T09:00:00Z',
        updatedAt: '2026-03-04T11:30:00Z',
        hasNewActivity: true, // <-- will show the pulsing blue dot
    },
    {
        id: 'chat-3',
        title: 'Объясни квантовые вычисления',
        createdAt: '2026-03-03T14:00:00Z',
        updatedAt: '2026-03-03T14:45:00Z',
        hasNewActivity: false,
    },
    {
        id: 'chat-4',
        title: 'Рецепт шоколадного торта',
        createdAt: '2026-03-03T18:00:00Z',
        updatedAt: '2026-03-03T18:20:00Z',
        hasNewActivity: true,
    },
    {
        id: 'chat-5',
        title: 'История Великого шёлкового',
        createdAt: '2026-03-02T10:00:00Z',
        updatedAt: '2026-03-02T10:55:00Z',
        hasNewActivity: false,
    },
];

// ─── Mock Messages (for chat-1) ───────────────────────────────────────────────

export const mockMessages: Message[] = [
    {
        id: 'msg-1',
        chatId: 'chat-1',
        role: 'user',
        content: 'Что такое нейронная сеть? Объясни просто.',
        createdAt: '2026-03-04T08:00:00Z',
    },
    {
        id: 'msg-2',
        chatId: 'chat-1',
        role: 'assistant',
        content: `## Нейронная сеть

Нейронная сеть — это модель машинного обучения, вдохновлённая работой человеческого мозга. Она состоит из **нейронов** (узлов), организованных в слои:

- **Входной слой** — получает данные
- **Скрытые слои** — преобразуют данные
- **Выходной слой** — выдаёт результат

### Простой пример на Python

\`\`\`python
import torch
import torch.nn as nn

class SimpleNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(784, 128),
            nn.ReLU(),
            nn.Linear(128, 10)
        )

    def forward(self, x):
        return self.layers(x)

model = SimpleNet()
print(model)
\`\`\`

Нейронные сети обучаются на примерах, корректируя веса связей с помощью **обратного распространения ошибки** (backpropagation).`,
        createdAt: '2026-03-04T08:01:00Z',
    },
    {
        id: 'msg-3',
        chatId: 'chat-1',
        role: 'user',
        content: 'А чем отличается глубокое обучение от обычного?',
        createdAt: '2026-03-04T08:05:00Z',
    },
    {
        id: 'msg-4',
        chatId: 'chat-1',
        role: 'assistant',
        content: `Отличие **глубокого обучения (Deep Learning)** от обычного машинного обучения (ML):

| Характеристика | ML | Deep Learning |
|---|---|---|
| Извлечение признаков | Вручную | Автоматически |
| Объём данных | Малый/средний | Большой |
| Интерпретируемость | Высокая | Низкая |
| Вычислительная мощь | Низкая | Высокая (GPU) |

> **Вывод:** Deep Learning — это подмножество ML, использующее нейронные сети с *множеством* скрытых слоёв (отсюда и "глубокое").`,
        createdAt: '2026-03-04T08:06:00Z',
    },
];
