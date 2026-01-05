import kivy
kivy.require('2.0.0')
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

import threading
import os

from eng1neer import load_all_definitions, respond_with_evidence, detailed_comparison, respond_subject_specific


def safe_format(text: str) -> str:
    return (text or '').strip()


class ChatBox(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        from kivy.core.window import Window
        Window.size = (420, 720)
        self.padding = 10
        self.spacing = 8
        self.accent_color = [0.22, 0.78, 0.51, 1]
        self.user_color = [0.18, 0.45, 0.85, 1]
        self.bot_color = self.accent_color
        self.font_name = 'Roboto'
        self.font_size = 16

        # History area
        self.history = Label(
            size_hint_y=None,
            text='',
            markup=True,
            font_name=self.font_name,
            font_size=self.font_size,
            color=[1, 1, 1, 1],
            halign='left',
            valign='top',
            text_size=(380, None),
            padding=(10, 10),
        )
        self.history.bind(texture_size=self._update_height)
        scroll = ScrollView(size_hint=(1, 0.82), bar_width=6)
        scroll.add_widget(self.history)
        self.add_widget(scroll)

        # Input
        self.input = TextInput(
            size_hint=(1, 0.10),
            multiline=False,
            font_name=self.font_name,
            font_size=self.font_size,
            background_color=[0.12, 0.14, 0.16, 1],
            foreground_color=[1, 1, 1, 1],
            padding=(10, 10),
        )
        self.input.bind(on_text_validate=self.on_enter)
        self.add_widget(self.input)

        # Buttons
        btn_row = BoxLayout(size_hint=(1, 0.06), orientation='horizontal', spacing=6)
        send_btn = Button(text='Send', background_color=self.accent_color, color=[0, 0, 0, 1])
        send_btn.bind(on_release=self.on_send)
        evidence_btn = Button(text='Show Evidence', background_color=[0.9, 0.9, 0.9, 1], color=[0, 0, 0, 1])
        evidence_btn.bind(on_release=self.on_show_evidence)
        btn_row.add_widget(send_btn)
        btn_row.add_widget(evidence_btn)
        self.add_widget(btn_row)

        # Load definitions (may be large); tolerate failure
        try:
            self.defs = load_all_definitions()
        except Exception:
            self.defs = {}

        self._last_prompt = None

    def _update_height(self, instance, value):
        self.history.height = self.history.texture_size[1]

    def on_enter(self, instance):
        self.send_message()

    def on_send(self, instance):
        self.send_message()

    def send_message(self):
        user_text = (self.input.text or '').strip()
        if not user_text:
            return
        self._last_prompt = user_text
        self.append_history(f"[b]You:[/b] {user_text}\n")
        self.input.text = ''
        threading.Thread(target=self._get_bot_response_thread, args=(user_text,), daemon=True).start()

    def _get_bot_response_thread(self, prompt: str):
        from kivy.clock import Clock

        def safe_append(text):
            import re
            text = re.sub(r'\[/?(color|b)[^\]]*\]', '', text)
            self.append_history(text)

        # If the prompt requests code, force the code engine to return code-only output
        if prompt.lower().startswith('code:') or prompt.lower().startswith('generate code'):
            raw = prompt.split(':', 1)[1].strip() if ':' in prompt else prompt
            fname = None
            rest = raw
            try:
                import re
                m = re.match(r'file[: ]+(\S+)\s*(.*)', raw, re.I)
                if m:
                    fname = m.group(1)
                    rest = m.group(2) or ''
            except Exception:
                pass
            directive = f"Generate only Python code, no explanation. {rest}".strip()
            try:
                from new_natural_code_engine import NaturalCodeEngine
                eng = NaturalCodeEngine('data')
                resp = eng.generate_code(directive)
                if fname:
                    from pathlib import Path
                    p = Path('examples')
                    p.mkdir(parents=True, exist_ok=True)
                    (p / fname).write_text(resp, encoding='utf-8')
            except Exception as e:
                resp = f'Code engine error: {e}'
        else:
            # Try the evidence-aware responder (verbose narrative)
            try:
                resp = respond_with_evidence(self.defs, prompt, verbose=True)
            except Exception:
                try:
                    resp = respond_subject_specific(prompt, assoc_path='thesaurus_assoc.json', data_dir='data')
                except Exception as e:
                    resp = f'Error in responder: {e}'

        out = safe_format(resp)
        if not out:
            out = 'Sorry, no response generated.'
        # truncate to reasonable size
        max_lines = 40
        lines = out.splitlines()
        if len(lines) > max_lines:
            out = '\n'.join(lines[:max_lines]) + '\n... [truncated]'

        Clock.schedule_once(lambda dt: safe_append(f"[color=00ff00][b]Anemone:[/b] {out}[/color]\n"))

    def append_history(self, text: str):
        if text is None:
            return
        if not isinstance(text, str):
            text = str(text)
        import re

        def bubble(msg, who='bot'):
            color = self.bot_color if who == 'bot' else self.user_color
            color_hex = ''.join(f'{int(c*255):02x}' for c in color[:3])
            if who == 'bot':
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

    def on_show_evidence(self, instance):
        if not self._last_prompt:
            self.append_history('[color=ff9900]No prompt has been sent yet.[/color]\n')
            return
        threading.Thread(target=self._fetch_and_show_evidence, args=(self._last_prompt,), daemon=True).start()

    def _fetch_and_show_evidence(self, prompt: str):
        from kivy.clock import Clock
        try:
            det = detailed_comparison(self.defs, prompt)
            if not isinstance(det, dict):
                Clock.schedule_once(lambda dt: self.append_history('[color=ff0000]No evidence available.[/color]\n'))
                return
            parts = []
            parts.append('[b]Evidence[/b]')
            parts.append(f"Predicate: {det.get('predicate')}")
            terms = det.get('terms', [])
            if terms:
                parts.append('Terms: ' + ', '.join(terms))
            supporting = det.get('supporting', {})
            unsupporting = det.get('unsupporting', {})
            if supporting:
                parts.append('\nSupporting fragments:')
                for t, frags in supporting.items():
                    parts.append(f" - {t}: {len(frags)} fragments")
                    for f in frags[:6]:
                        parts.append(f"    • {f}")
            if unsupporting:
                parts.append('\nUnsupporting fragments:')
                for t, frags in unsupporting.items():
                    parts.append(f" - {t}: {len(frags)} fragments")
                    for f in frags[:6]:
                        parts.append(f"    • {f}")
            out = '\n'.join(parts)
            Clock.schedule_once(lambda dt: self.append_history(f"[color=ffff66]{out}[/color]\n"))
        except Exception as e:
            import traceback
            err = f"[color=ff0000]Evidence error: {e}\n{traceback.format_exc()}[/color]\n"
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: self.append_history(err))


class ChatApp(App):
    def build(self):
        return ChatBox()


if __name__ == '__main__':
    ChatApp().run()
import kivy
kivy.require('2.0.0')
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

import threading

from eng1neer import (
    load_all_definitions,
    respond_with_evidence,
    detailed_comparison,
    try_eval_expression,
    respond_subject_specific,
)


def safe_format(text: str) -> str:
    return (text or '').strip()


class ChatBox(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        from kivy.core.window import Window
        Window.size = (420, 720)
        self.padding = 10
        self.spacing = 8
        self.accent_color = [0.22, 0.78, 0.51, 1]
        self.user_color = [0.18, 0.45, 0.85, 1]
        self.bot_color = self.accent_color
        self.font_name = 'Roboto'
        self.font_size = 16

        self.history = Label(
            size_hint_y=None,
            text='',
            markup=True,
            font_name=self.font_name,
            font_size=self.font_size,
            color=[1, 1, 1, 1],
            halign='left',
            valign='top',
            text_size=(380, None),
            padding=(10, 10),
        )
        self.history.bind(texture_size=self._update_height)
        scroll = ScrollView(size_hint=(1, 0.82), bar_width=6)
        scroll.add_widget(self.history)
        self.add_widget(scroll)

        self.input = TextInput(
            size_hint=(1, 0.10),
            multiline=False,
            font_name=self.font_name,
            font_size=self.font_size,
            background_color=[0.12, 0.14, 0.16, 1],
            foreground_color=[1, 1, 1, 1],
            padding=(10, 10),
        )
        self.input.bind(on_text_validate=self.on_enter)
        self.add_widget(self.input)

        btn_row = BoxLayout(size_hint=(1, 0.06), orientation='horizontal', spacing=6)
        send_btn = Button(text='Send', background_color=self.accent_color, color=[0, 0, 0, 1])
        send_btn.bind(on_release=self.on_send)
        evidence_btn = Button(text='Show Evidence', background_color=[0.9, 0.9, 0.9, 1], color=[0, 0, 0, 1])
        evidence_btn.bind(on_release=self.on_show_evidence)
        btn_row.add_widget(send_btn)
        btn_row.add_widget(evidence_btn)
        self.add_widget(btn_row)

        # Load definitions (may be large). Use the derived Wikipedia defs first.
        try:
            self.defs = load_all_definitions()
        except Exception:
            self.defs = {}

        self._last_prompt = None

    def _update_height(self, instance, value):
        self.history.height = self.history.texture_size[1]

    def on_enter(self, instance):
        self.send_message()

    def on_send(self, instance):
        self.send_message()

    def send_message(self):
        user_text = (self.input.text or '').strip()
        if not user_text:
            return
        self._last_prompt = user_text
        self.append_history(f"[b]You:[/b] {user_text}\n")
        self.input.text = ''
        threading.Thread(target=self._get_bot_response_thread, args=(user_text,), daemon=True).start()

    def _get_bot_response_thread(self, prompt: str):
        from kivy.clock import Clock

        def safe_append(text):
            import re
            text = re.sub(r'\[/?(color|b)[^\]]*\]', '', text)
            self.append_history(text)

        # Try the evidence-aware responder (verbose narrative)
        try:
            resp = respond_with_evidence(self.defs, prompt, verbose=True)
        except Exception:
            try:
                resp = respond_subject_specific(prompt, assoc_path='thesaurus_assoc.json', data_dir='data')
            except Exception as e:
                resp = f'Error in responder: {e}'

        out = safe_format(resp)
        if not out:
            out = 'Sorry, no response generated.'
        # truncate to reasonable size
        max_lines = 40
        lines = out.splitlines()
        if len(lines) > max_lines:
            out = '\n'.join(lines[:max_lines]) + '\n... [truncated]'

        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: safe_append(f"[color=00ff00][b]Anemone:[/b] {out}[/color]\n"))

    def append_history(self, text: str):
        if text is None:
            return
        if not isinstance(text, str):
            text = str(text)
        import re

        def bubble(msg, who='bot'):
            color = self.bot_color if who == 'bot' else self.user_color
            color_hex = ''.join(f'{int(c*255):02x}' for c in color[:3])
            if who == 'bot':
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

    def on_show_evidence(self, instance):
        if not self._last_prompt:
            self.append_history('[color=ff9900]No prompt has been sent yet.[/color]\n')
            return
        threading.Thread(target=self._fetch_and_show_evidence, args=(self._last_prompt,), daemon=True).start()

    def _fetch_and_show_evidence(self, prompt: str):
        from kivy.clock import Clock
        try:
            det = detailed_comparison(self.defs, prompt)
            if not isinstance(det, dict):
                Clock.schedule_once(lambda dt: self.append_history('[color=ff0000]No evidence available.[/color]\n'))
                return
            parts = []
            parts.append('[b]Evidence[/b]')
            parts.append(f"Predicate: {det.get('predicate')}")
            terms = det.get('terms', [])
            if terms:
                parts.append('Terms: ' + ', '.join(terms))
            supporting = det.get('supporting', {})
            unsupporting = det.get('unsupporting', {})
            if supporting:
                parts.append('\nSupporting fragments:')
                for t, frags in supporting.items():
                    parts.append(f" - {t}: {len(frags)} fragments")
                    for f in frags[:6]:
                        parts.append(f"    • {f}")
            if unsupporting:
                parts.append('\nUnsupporting fragments:')
                for t, frags in unsupporting.items():
                    parts.append(f" - {t}: {len(frags)} fragments")
                    for f in frags[:6]:
                        parts.append(f"    • {f}")
            out = '\n'.join(parts)
            Clock.schedule_once(lambda dt: self.append_history(f"[color=ffff66]{out}[/color]\n"))
        except Exception as e:
            import traceback
            err = f"[color=ff0000]Evidence error: {e}\n{traceback.format_exc()}[/color]\n"
            Clock.schedule_once(lambda dt: self.append_history(err))


class ChatApp(App):
    def build(self):
        return ChatBox()


if __name__ == '__main__':
    ChatApp().run()
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
        import kivy
        kivy.require('2.0.0')
        from kivy.app import App
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.textinput import TextInput
        from kivy.uix.button import Button
        from kivy.uix.label import Label
        from kivy.uix.scrollview import ScrollView

        import threading

        from eng1neer import respond_subject_specific, try_eval_expression


        def process_input(line: str, assoc_path: str = 'thesaurus_assoc.json') -> str:
            line = (line or '').strip()
            if not line:
                return ''
            _ll = line.lower()
            # date command
            if _ll.startswith('date '):
                parts = line.split()[1:]
                try:
                    from date_calculator import cli as date_cli
                    date_cli(parts)
                    return ''
                except Exception as e:
                    return f'Date command failed: {e}'
            if _ll.startswith('verify '):
                parts = line.split()[1:]
                try:
                    from equality_verifier import cli as verify_cli
                    verify_cli(parts)
                    return ''
                except Exception as e:
                    return f'Verify command failed: {e}'

            if _ll.startswith('code:') or _ll.startswith('generate code'):
                raw = line.split(':', 1)[1].strip() if ':' in line else line
                fname = None
                rest = raw
                try:
                    import re
                    m = re.match(r'file[: ]+(\S+)\s*(.*)', raw, re.I)
                    if m:
                        fname = m.group(1)
                        rest = m.group(2) or ''
                except Exception:
                    pass
                directive = f"Generate only Python code, no explanation. {rest}".strip()
                if 'code_engine' not in globals():
                    try:
                        from new_natural_code_engine import NaturalCodeEngine
                        globals()['code_engine'] = NaturalCodeEngine('data')
                    except Exception as e:
                        return f'Code engine load failed: {e}'
                try:
                    code = globals()['code_engine'].generate_code(directive)
                    if fname:
                        from pathlib import Path
                        p = Path('examples')
                        p.mkdir(parents=True, exist_ok=True)
                        (p / fname).write_text(code, encoding='utf-8')
                    return code
                except Exception as e:
                    return f'Code generation failed: {e}'

            if '=' in line:
                try:
                    from sympy import Eq, solve, sympify
                    eqs = [eq.strip() for eq in line.split(',') if '=' in eq]
                    if len(eqs) > 10:
                        eqs = eqs[:10]
                    sympy_eqs = []
                    all_vars = set()
                    for eq in eqs:
                        left, right = eq.split('=', 1)
                        left_expr = sympify(left)
                        right_expr = sympify(right)
                        sympy_eqs.append(Eq(left_expr, right_expr))
                        all_vars.update(left_expr.free_symbols)
                        all_vars.update(right_expr.free_symbols)
                    sol = solve(sympy_eqs, list(all_vars), dict=True)
                    if sol:
                        outs = []
                        for s in sol:
                            out = ', '.join(f"{str(k)} = {v}" for k, v in s.items())
                            outs.append(out)
                        return '\n'.join(outs)
                    return 'No solution found.'
                except Exception as e:
                    return f'Could not solve equation(s): {e}'

            if any(c in line for c in '+-*/^()') and any(ch.isdigit() for ch in line):
                try:
                    res = try_eval_expression(line)
                    return str(res) if res is not None else 'Invalid math expression.'
                except Exception:
                    return 'Invalid math expression.'

            # default: subject-specific response
            try:
                return respond_subject_specific(line, assoc_path=assoc_path, data_dir='data')
            except Exception as e:
                return f'Error in responder: {e}'


        def get_response(prompt):
            return process_input(prompt)


        class ChatBox(BoxLayout):
            def __init__(self, **kwargs):
                super().__init__(orientation='vertical', **kwargs)
                from kivy.core.window import Window
                Window.size = (360, 640)
                self.padding = 10
                self.spacing = 8
                self.bg_color = [0.09, 0.11, 0.13, 1]
                self.accent_color = [0.22, 0.78, 0.51, 1]
                self.user_color = [0.18, 0.45, 0.85, 1]
                self.bot_color = self.accent_color
                self.font_name = 'Roboto'
                self.font_size = 17

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
                    import re
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
                import sys
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
