import os
import shutil
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle

class ModernButton(Button):
    def __init__(self, bg_color, text_color='#FFFFFF', **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0, 0, 0, 0)
        self.color = get_color_from_hex(text_color)
        self.base_color = get_color_from_hex(bg_color)
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(rgba=(self.base_color if self.state == 'normal' else [c*1.1 for c in self.base_color[:3]] + [1]))
            RoundedRectangle(pos=(self.x + dp(2), self.y + dp(2)), 
                             size=(self.width - dp(4), self.height - dp(4)), 
                             radius=[dp(12)])

class CalcScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.clearcolor = get_color_from_hex('#000000')
        layout = BoxLayout(orientation='vertical', padding=[dp(8), dp(5), dp(8), dp(8)], spacing=dp(2))
        self.res = Label(text="0", font_size=dp(70), bold=True, size_hint_y=0.45, 
                         halign='right', valign='bottom', text_size=(Window.width - dp(30), None))
        layout.add_widget(self.res)
        grid = GridLayout(cols=4, spacing=dp(3), size_hint_y=None, height=dp(360))
        btns = [
            ('AC', '#262626', '#FF8C00'), ('DEL', '#262626', '#FF8C00'), ('%', '#262626', '#FF8C00'), ('÷', '#262626', '#FF8C00'),
            ('7', '#1C1C1C', '#FFFFFF'), ('8', '#1C1C1C', '#FFFFFF'), ('9', '#1C1C1C', '#FFFFFF'), ('×', '#262626', '#FF8C00'),
            ('4', '#1C1C1C', '#FFFFFF'), ('5', '#1C1C1C', '#FFFFFF'), ('6', '#1C1C1C', '#FFFFFF'), ('-', '#262626', '#FF8C00'),
            ('1', '#1C1C1C', '#FFFFFF'), ('2', '#1C1C1C', '#FFFFFF'), ('3', '#1C1C1C', '#FFFFFF'), ('+', '#262626', '#FF8C00'),
            ('⚙️', '#1C1C1C', '#FFFFFF'), ('0', '#1C1C1C', '#FFFFFF'), ('.', '#1C1C1C', '#FFFFFF'), ('=', '#FF8C00', '#FFFFFF')
        ]
        for t, bg, tc in btns:
            b = ModernButton(text=t, bg_color=bg, text_color=tc, font_size=dp(24), size_hint_y=None, height=dp(70))
            b.bind(on_press=self.press)
            grid.add_widget(b)
        layout.add_widget(grid)
        self.add_widget(layout)

    def press(self, inst):
        v = inst.text
        cur = self.res.text
        if v == '=':
            if cur == '1998+11+17': 
                self.manager.current = 'vault1'
                self.res.text = '0'
            else:
                try: self.res.text = str(eval(cur.replace('×','*').replace('÷','/')))
                except: self.res.text = "Xato"
        elif v == 'AC': self.res.text = '0'
        elif v == 'DEL': self.res.text = cur[:-1] if len(cur)>1 else '0'
        else: self.res.text = v if cur == '0' else cur + v

class VaultScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        l = BoxLayout(orientation='vertical', padding=dp(20))
        l.add_widget(Label(text="MAXFIY OMBOR", font_size=dp(30), color=[1,0,0,1]))
        l.add_widget(Button(text="Orqaga", size_hint_y=None, height=dp(50), on_press=lambda x: setattr(self.manager, 'current', 'calc')))
        self.add_widget(l)

class MainApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(CalcScreen(name='calc'))
        sm.add_widget(VaultScreen(name='vault1'))
        return sm

if __name__ == '__main__':
    MainApp().run()
