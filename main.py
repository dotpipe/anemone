import kivy
kivy.require('2.0.0')
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

import threading

def get_response(prompt):
    # Import your engine here
    try:
        from eng1neer import respond_subject_specific
        return respond_subject_specific(prompt)
    except Exception as e:
        return f"Error: {e}"

class ChatBox(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        from kivy.core.window import Window
        # Set default window size for desktop (Moto G aspect: 360x640)
        Window.size = (360, 640)
        self.padding = 10
        self.spacing = 8
        self.bg_color = [0.09, 0.11, 0.13, 1]  # dark background
        self.accent_color = [0.22, 0.78, 0.51, 1]  # soft green accent
        self.user_color = [0.18, 0.45, 0.85, 1]  # blue for user
        self.bot_color = self.accent_color
        self.font_name = 'Roboto'
        self.font_size = 17
        # History area
        self.history = Label(
            size_hint_y=None,
            text='',
            markup=True,
            font_name=self.font_name,
            font_size=self.font_size,
            color=[1,1,1,1],
            halign='left',
            valign='top',
            text_size=(340, None),
            padding=(10, 10)
        )
        self.history.bind(texture_size=self._update_height)
        scroll = ScrollView(size_hint=(1, 0.82), bar_width=6, scroll_type=['bars', 'content'])
        scroll.add_widget(self.history)
        self.add_widget(scroll)
        # Input area
        self.input = TextInput(
            size_hint=(1, 0.10),
            multiline=False,
            font_name=self.font_name,
            font_size=self.font_size,
            background_color=[0.15,0.17,0.19,1],
            foreground_color=[1,1,1,1],
            padding=(10,10),
            cursor_color=self.accent_color
        )
        self.input.bind(on_text_validate=self.on_enter)
        self.add_widget(self.input)
        send_btn = Button(
            text='Send',
            size_hint=(1, 0.06),
            background_color=self.accent_color,
            color=[0,0,0,1],
            font_name=self.font_name,
            font_size=self.font_size+1,
            bold=True
        )
        send_btn.bind(on_release=self.on_send)
        self.add_widget(send_btn)

    def _update_height(self, instance, value):
        self.history.height = self.history.texture_size[1]

    def on_enter(self, instance):
        self.send_message()

    def on_send(self, instance):
        self.send_message()

    def send_message(self):
        user_text = self.input.text.strip()
        if not user_text:
            return
        self.append_history(f"[b]You:[/b] {user_text}\n")
        self.input.text = ''
        threading.Thread(target=self.get_bot_response, args=(user_text,), daemon=True).start()

    def get_bot_response(self, prompt):
        from kivy.clock import Clock
        def safe_append(text):
            # Sanitize markup: remove any stray [color] or [b] tags that aren't closed
            import re
            # Remove any unmatched opening/closing tags
            text = re.sub(r'\[/?(color|b)[^\]]*\]', '', text)
            self.append_history(text)
        try:
            response = get_response(prompt)
            cleaned = response.strip()
            cleaned = '\n'.join([line for line in cleaned.splitlines() if line.strip()])
            if not cleaned:
                cleaned = "Sorry, no response was generated."
            max_lines = 20
            lines = cleaned.splitlines()
            if len(lines) > max_lines:
                cleaned = '\n'.join(lines[:max_lines]) + '\n... [truncated]'
            Clock.schedule_once(lambda dt: safe_append(f"[color=00ff00][b]Anemone:[/b] {cleaned}[/color]\n"))
        except Exception as e:
            import traceback
            err_msg = f"[color=ff0000][b]Error:[/b] {str(e)}\n{traceback.format_exc()}[/color]\n"
            Clock.schedule_once(lambda dt: safe_append(err_msg))

    def append_history(self, text):
        # Prevent accidental clearing or overwriting
        import sys
        print(f"[DEBUG] Appending to chat history: {repr(text)}", file=sys.stderr)
        if text is None:
            return
        if not isinstance(text, str):
            text = str(text)
        import re
        def bubble(msg, who='bot'):
            color = self.bot_color if who=='bot' else self.user_color
            color_hex = ''.join(f'{int(c*255):02x}' for c in color[:3])
            if who=='bot':
                return f"[color=#{color_hex}][b]{msg}[/b][/color]"
            else:
                return f"[color=#{color_hex}]{msg}[/color]"
        try:
            if text.startswith('[b]You:'):
                msg = re.sub(r'\[/?b\]', '', text).replace('You:', '').strip()
                self.history.text = (self.history.text or '') + bubble(f'You: {msg}\n', 'user')
            elif text.startswith('[color=00ff00][b]Anemone:'):
                msg = re.sub(r'\[/?b\]', '', text).replace('Anemone:', '').replace('[/color]', '').strip()
                self.history.text = (self.history.text or '') + bubble(f'Anemone: {msg}\n', 'bot')
            else:
                self.history.text = (self.history.text or '') + text
        except Exception as e:
            import traceback
            err_msg = f"[color=ff0000][b]UI Error:[/b] {str(e)}\n{traceback.format_exc()}[/color]\n"
            self.history.text = (self.history.text or '') + err_msg

class ChatApp(App):
    def build(self):
        return ChatBox()

if __name__ == '__main__':
    ChatApp().run()