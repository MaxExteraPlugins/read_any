__id__ = "read_any"
__name__ = "Read Any"
__description__ = "Позволяет прочитать выбранные чаты одной кнопкой или автоматически. Добавляйте чаты через меню трех точек в чате (⋮ → Плагины). Управляйте через настройки плагина."
__author__ = "@itNotMax - @MaxExteraPlugins"
__version__ = "1.8.0"
__min_version__ = "12.10.6"
__app_version__ = ">=12.5.1"
__sdk_version__ = ">=1.4.3.3"
__icon__ = "MaxExteraPluginsStickers/13"

from base_plugin import BasePlugin, MenuItemData, MenuItemType
from client_utils import (
    get_messages_controller,
    get_messages_storage,
    get_notification_center,
    get_last_fragment,
)
from android_utils import run_on_ui_thread, OnClickListener
from ui.bulletin import BulletinHelper
from ui.settings import Header, Text, Divider, Switch, Selector
from hook_utils import find_class, get_private_field
from java import jclass, dynamic_proxy
from typing import Dict, Any, List
import json

BUTTON_ID = 229


def _is_home_dialogs(fragment):
    try:
        if fragment is None:
            return False
        class_name = fragment.getClass().getName()
        if class_name != "org.telegram.ui.DialogsActivity":
            return False
        try:
            folder_id = int(fragment.folderId)
            if folder_id != 0:
                return False
        except Exception:
            pass
        try:
            only_select = bool(fragment.onlySelect)
            if only_select:
                return False
        except Exception:
            pass
        return True
    except Exception:
        return False


def _has_sliding_fragment(fragment):
    try:
        container = fragment.rightSlidingDialogContainer
        if container is not None:
            try:
                if container.hasFragment():
                    return True
            except Exception:
                cf = get_private_field(container, "currentFragment")
                if cf is not None:
                    return True
    except Exception:
        pass
    return False


def _find_home_fragment():
    try:
        f = get_last_fragment()
        if f is not None and _is_home_dialogs(f):
            return f
    except Exception:
        pass
    try:
        f = get_last_fragment()
        if f is not None:
            layout = f.getParentLayout()
            if layout is not None:
                stack = layout.getFragmentStack()
                if stack is not None:
                    for i in range(stack.size()):
                        sf = stack.get(i)
                        if _is_home_dialogs(sf):
                            return sf
    except Exception:
        pass
    try:
        LaunchActivity = jclass("org.telegram.ui.LaunchActivity")
        f = LaunchActivity.getLastFragment()
        if f is not None and _is_home_dialogs(f):
            return f
    except Exception:
        pass
    try:
        LaunchActivity = jclass("org.telegram.ui.LaunchActivity")
        activity = LaunchActivity.instance
        if activity is not None:
            stack = activity.mainFragmentsStack
            if stack is not None:
                for i in range(stack.size()):
                    f = stack.get(i)
                    if _is_home_dialogs(f):
                        return f
    except Exception:
        pass
    try:
        LaunchActivity = jclass("org.telegram.ui.LaunchActivity")
        activity = LaunchActivity.instance
        if activity is not None:
            layout = activity.getActionBarLayout()
            if layout is not None:
                stack = layout.getFragmentStack()
                if stack is not None:
                    for i in range(stack.size()):
                        f = stack.get(i)
                        if _is_home_dialogs(f):
                            return f
    except Exception:
        pass
    return None


class DialogsCreateViewHook:
    def __init__(self, plugin):
        self.plugin = plugin

    def after_hooked_method(self, param):
        try:
            fragment = param.thisObject
            if not _is_home_dialogs(fragment):
                return
            self.plugin._sliding_open = False
            self.plugin._injected_btn = None
            run_on_ui_thread(lambda: self.plugin._inject_button(fragment), 300)
        except Exception:
            pass


class DialogsResumeHook:
    def __init__(self, plugin):
        self.plugin = plugin

    def after_hooked_method(self, param):
        try:
            fragment = param.thisObject
            if not _is_home_dialogs(fragment):
                return
            if _has_sliding_fragment(fragment):
                return
            run_on_ui_thread(lambda: self.plugin._inject_button(fragment), 100)
        except Exception:
            pass


class DialogsFullyVisibleHook:
    def __init__(self, plugin):
        self.plugin = plugin

    def after_hooked_method(self, param):
        try:
            fragment = param.thisObject
            if not _is_home_dialogs(fragment):
                return
            if _has_sliding_fragment(fragment):
                return
            run_on_ui_thread(lambda: self.plugin._inject_button(fragment), 200)
        except Exception:
            pass


class SlidingPresentHook:
    def __init__(self, plugin):
        self.plugin = plugin

    def after_hooked_method(self, param):
        try:
            self.plugin._on_sliding_opened()
        except Exception:
            pass


class SlidingFinishPreviewHook:
    def __init__(self, plugin):
        self.plugin = plugin

    def after_hooked_method(self, param):
        try:
            self.plugin._on_sliding_closed()
        except Exception:
            pass



# ============================================================
# MaxExteraPlugins Shared Author & Channel Subscription Module
# ============================================================

# ============================================================
# MaxExteraPlugins Shared Author & Channel Subscription Module
# ============================================================
class AuthorChannelHelper:
    CONFIG_URL = "https://raw.githubusercontent.com/MaxExteraPlugins/config/main/links.json"

    DEFAULT_LINKS = {
        "channel_username": "MaxExteraPlugins",
        "channel_url": "https://t.me/MaxExteraPlugins",
        "trial_days": 7,
        "header": {"ru": "MaxExteraPlugins", "en": "MaxExteraPlugins"},
        "buttons": [
            {"title": {"ru": "Канал автора", "en": "Author's Channel"}, "icon": "msg_channel", "url": "https://t.me/MaxExteraPlugins"},
            {"title": {"ru": "Поддержать автора", "en": "Support author"}, "icon": "msg_share", "url": "https://t.me/itNotMax"},
            {"title": {"ru": "Сообщить о баге", "en": "Report a bug"}, "icon": "msg_help", "url": "https://t.me/itNotMax"}
        ]
    }

    _TEXTS = {
        "install_card_title": {"ru": "Спасибо за установку!", "en": "Thank you for installing!"},
        "install_card_msg": {
            "ru": "Надеемся, что плагин будет вам полезен!\n\nМы делаем плагины бесплатными и доступными для всех: пожалуйста, поддержите нас подпиской. Там будут только важные новости, обновления и розыгрыши.",
            "en": "We hope this plugin will be useful to you!\n\nWe keep our plugins free and open for everyone: please support us with a subscription. We only post key news, updates, and giveaways."
        },
        "subscribe_btn": {"ru": "Подписаться", "en": "Subscribe"},
        "remind_later_btn": {"ru": "Напомнить позже", "en": "Remind later"},
        "check_sub_btn": {"ru": "Проверить подписку", "en": "Check subscription"},
        "trial_expired_title": {"ru": "Пожалуйста, подпишитесь на канал", "en": "Please subscribe to the channel"},
        "trial_expired_msg": {
            "ru": "Пожалуйста, подпишитесь на наш официальный канал.\n\nМы делаем плагины бесплатно, ничего не требуя взамен. До подписки функции плагина временно приостановлены.",
            "en": "Please subscribe to our official channel.\n\nWe develop plugins for free and ask nothing in return. Plugin features are paused until you subscribe."
        },
        "sub_thank_you": {"ru": "Спасибо за подписку на наш канал!", "en": "Thank you for subscribing to our channel!"},
        "sub_thank_you_after_expired": {"ru": "Спасибо за подписку на наш канал!\nПлагин продолжит работу!", "en": "Thank you for subscribing to our channel!\nThe plugin will continue working!"},
        "sub_not_found": {"ru": "Подписка не обнаружена. Пожалуйста, подпишитесь на канал.", "en": "Subscription not found. Please subscribe to the channel."},
        "settings_channel": {"ru": "Канал автора", "en": "Author's Channel"},
        "settings_donate": {"ru": "Поддержать автора", "en": "Support author"},
        "settings_bug_report": {"ru": "Сообщить о баге", "en": "Report a bug"}
    }

    @classmethod
    def is_ru(cls) -> bool:
        try:
            from org.telegram.messenger import LocaleController
            cur = str(LocaleController.getInstance().getCurrentLocale().getLanguage() or "").lower()
            if cur.startswith(("ru", "uk", "be")): return True
            if cur: return False
        except Exception:
            pass
        try:
            from java.util import Locale
            code = str(Locale.getDefault().getLanguage() or "").lower()
            if code.startswith(("ru", "uk", "be")): return True
        except Exception:
            pass
        return False

    @classmethod
    def tr(cls, key: str) -> str:
        entry = cls._TEXTS.get(key, {})
        return entry.get("ru" if cls.is_ru() else "en", entry.get("en", key))

    def __init__(self, plugin, icon_sticker=None):
        self.plugin = plugin
        self.icon_sticker = icon_sticker or getattr(plugin, "__icon__", "MaxExteraPluginsStickers/1")
        self._stopped = False
        self._active_dialog = None
        self._last_known_sub = None

    def on_load(self):
        self._stopped = False
        self._active_dialog = None
        self._last_known_sub = None
        self._load_remote_links_async()
        self._check_initial_subscription_flow()
        self._start_subscription_watcher()

    def on_event(self, event_type):
        try:
            name = str(event_type).upper()
            if name.endswith("START") or name.endswith("RESUME"):
                self._check_subscription_change_instant()
        except Exception:
            pass

    def on_unload(self):
        self._stopped = True
        self._dismiss_active_dialog()

    def _get_links(self) -> dict:
        raw = self.plugin.get_setting("remote_links_cache", None)
        if raw:
            try:
                import json
                data = json.loads(raw)
                if isinstance(data, dict): return data
            except Exception:
                pass
        return self.DEFAULT_LINKS

    def _load_remote_links_async(self):
        def worker():
            try:
                import urllib.request, json
                req = urllib.request.Request(self.CONFIG_URL, headers={"User-Agent": "MaxExteraPlugins"})
                with urllib.request.urlopen(req, timeout=4) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        if isinstance(data, dict):
                            self.plugin.set_setting("remote_links_cache", json.dumps(data))
                            self._resolve_channel_in_telegram(data.get("channel_username", "MaxExteraPlugins"))
            except Exception:
                pass
        import threading
        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def _open_url(self, url: str, view=None):
        try:
            from org.telegram.messenger.browser import Browser
            from org.telegram.messenger import ApplicationLoader
            from client_utils import get_last_fragment
            ctx = None
            if view is not None:
                ctx = view.getContext()
            if ctx is None:
                frag = get_last_fragment()
                if frag is not None:
                    ctx = frag.getParentActivity()
            if ctx is None:
                ctx = ApplicationLoader.applicationContext
            Browser.openUrl(ctx, url)
        except Exception:
            pass

    def _resolve_channel_in_telegram(self, username: str):
        try:
            from org.telegram.messenger import UserConfig, MessagesController
            from org.telegram.tgnet import TLRPC, ConnectionsManager, RequestDelegate
            clean_user = username.lstrip("@")
            acc = int(UserConfig.selectedAccount)
            mc = MessagesController.getInstance(acc)
            if not mc: return
            req = TLRPC.TL_contacts_resolveUsername()
            req.username = clean_user
            helper_ref = self
            class Delegate(RequestDelegate):
                def run(self, response, error):
                    if error is None and response is not None:
                        chats = getattr(response, "chats", None)
                        if chats is not None and chats.size() > 0:
                            mc.putChats(chats, False)
                            c = chats.get(0)
                            cid = getattr(c, "id", 0)
                            if cid > 0:
                                helper_ref.plugin.set_setting("resolved_channel_id", int(cid))
            ConnectionsManager.getInstance(acc).sendRequest(req, Delegate())
        except Exception:
            pass

    def is_subscribed(self) -> bool:
        try:
            from org.telegram.messenger import UserConfig, MessagesController
            links = self._get_links()
            target = str(links.get("channel_username", "MaxExteraPlugins") or "MaxExteraPlugins").lower().lstrip("@")
            saved_cid = self.plugin.get_setting("resolved_channel_id", 0)

            for acc in range(UserConfig.MAX_ACCOUNT_COUNT):
                uconf = UserConfig.getInstance(acc)
                if not uconf.isClientActivated(): continue
                mc = MessagesController.getInstance(acc)
                if not mc: continue

                if saved_cid:
                    try:
                        from java.lang import Long as JLong
                        c = mc.getChat(JLong(int(saved_cid)))
                        if c is not None:
                            left = bool(getattr(c, "left", True))
                            kicked = bool(getattr(c, "kicked", False))
                            if not left and not kicked: return True
                    except Exception:
                        pass

                try:
                    chat = mc.getUserOrChat(target)
                    if chat is not None:
                        cid = getattr(chat, "id", 0)
                        if cid and not saved_cid:
                            self.plugin.set_setting("resolved_channel_id", int(cid))
                        left = bool(getattr(chat, "left", True))
                        kicked = bool(getattr(chat, "kicked", False))
                        if not left and not kicked: return True
                except Exception:
                    pass

                try:
                    dialogs = mc.allDialogs
                    if dialogs is not None:
                        limit = min(dialogs.size(), 300)
                        for i in range(limit):
                            d = dialogs.get(i)
                            did = getattr(d, "id", 0)
                            if did < 0:
                                from java.lang import Long as JLong
                                c = mc.getChat(JLong(-did))
                                if c is not None:
                                    uname = str(getattr(c, "username", "") or "").lower()
                                    if uname == target:
                                        cid = getattr(c, "id", 0)
                                        if cid and not saved_cid:
                                            self.plugin.set_setting("resolved_channel_id", int(cid))
                                        left = bool(getattr(c, "left", True))
                                        kicked = bool(getattr(c, "kicked", False))
                                        if not left and not kicked: return True
                except Exception:
                    pass
        except Exception:
            pass
        return False

    def is_allowed(self) -> bool:
        import time
        if self.is_subscribed():
            if not self.plugin.get_setting("was_subscribed", False):
                was_exp = bool(self.plugin.get_setting("was_expired_state", False))
                self.plugin.set_setting("was_subscribed", True)
                self.plugin.set_setting("was_expired_state", False)
                self._notify_subscribed(was_expired=was_exp)
            return True

        if self.plugin.get_setting("was_expired_state", False) or self.plugin.get_setting("was_subscribed", False):
            self.plugin.set_setting("was_subscribed", False)
            self.plugin.set_setting("was_expired_state", True)
            self._show_expired_card()
            return False

        now = time.time()
        install_time = float(self.plugin.get_setting("install_time", 0.0) or 0.0)
        if install_time <= 0:
            install_time = now
            self.plugin.set_setting("install_time", install_time)

        trial_days = float(self._get_links().get("trial_days", 7))
        trial_sec = trial_days * 86400.0

        if (now - install_time) < trial_sec:
            return True

        self.plugin.set_setting("was_expired_state", True)
        self._show_expired_card()
        return False

    def prepend_settings(self, original_items=None) -> list:
        from ui.settings import Header, Text, Divider

        # Prevent double-prepending
        if original_items and any(getattr(x, "text", "") == "MaxExteraPlugins" for x in original_items if type(x).__name__ == "Header"):
            return original_items

        links = self._get_links()
        buttons_config = links.get("buttons")

        author_items = []
        if isinstance(buttons_config, list):
            for btn in buttons_config:
                if not isinstance(btn, dict): continue
                url = str(btn.get("url") or "").strip()
                if not url: continue

                title_data = btn.get("title")
                if isinstance(title_data, dict):
                    title = title_data.get("ru" if self.is_ru() else "en") or title_data.get("en") or title_data.get("ru") or ""
                elif isinstance(title_data, str) and title_data:
                    title = title_data
                else:
                    title = btn.get("title_ru" if self.is_ru() else "title_en") or btn.get("title_ru") or btn.get("title_en") or ""

                if not title: continue
                icon = str(btn.get("icon") or "msg_channel").strip()

                def make_click(u):
                    return lambda v=None: self._open_url(u, v)

                author_items.append(Text(text=title, icon=icon, on_click=make_click(url)))
        else:
            for k, text_key, icon_name in [
                ("channel_url", "settings_channel", "msg_channel"),
                ("donate_url", "settings_donate", "msg_share"),
                ("bug_report_url", "settings_bug_report", "msg_help")
            ]:
                u = str(links.get(k) or "").strip()
                if u:
                    author_items.append(Text(text=self.tr(text_key), icon=icon_name, on_click=lambda v=None, target_u=u: self._open_url(target_u, v)))

        res = []
        if author_items:
            hdr = links.get("header") or "MaxExteraPlugins"
            if isinstance(hdr, dict):
                hdr_text = hdr.get("ru" if self.is_ru() else "en") or hdr.get("ru") or hdr.get("en") or "MaxExteraPlugins"
            else:
                hdr_text = str(hdr)
            res.append(Header(text=hdr_text))
            res.extend(author_items)
            res.append(Divider())

        # Clean original_items by removing any old "Информация" / "Information" category
        cleaned_items = []
        if original_items:
            skipping_info = False
            for item in original_items:
                item_cls = type(item).__name__
                if item_cls == "Header":
                    txt = str(getattr(item, "text", "") or getattr(item, "title", "") or "").lower()
                    if "информ" in txt or "inform" in txt:
                        skipping_info = True
                        continue
                    else:
                        skipping_info = False
                elif skipping_info and item_cls == "Divider":
                    skipping_info = False
                    continue

                if not skipping_info:
                    cleaned_items.append(item)

        res.extend(cleaned_items)
        return res

    def _dismiss_active_dialog(self):
        try:
            if self._active_dialog is not None:
                self._active_dialog.dismiss()
        except Exception:
            pass
        self._active_dialog = None

    def _is_dialog_active(self) -> bool:
        try:
            if self._active_dialog is not None:
                return bool(self._active_dialog.isShowing())
        except Exception:
            pass
        return False

    def _notify_subscribed(self, was_expired=False):
        self.plugin.set_setting("was_subscribed", True)
        from ui.bulletin import BulletinHelper
        msg_key = "sub_thank_you_after_expired" if was_expired else "sub_thank_you"
        BulletinHelper.show_success(self.tr(msg_key))

    def _check_subscription_change_instant(self):
        try:
            from android_utils import run_on_ui_thread
            cur_sub = self.is_subscribed()
            prev_sub = self._last_known_sub
            if prev_sub is not None and prev_sub != cur_sub:
                self._last_known_sub = cur_sub
                if cur_sub:
                    was_exp = bool(self.plugin.get_setting("was_expired_state", False))
                    self.plugin.set_setting("was_subscribed", True)
                    self.plugin.set_setting("was_expired_state", False)
                    self._dismiss_active_dialog()
                    self._notify_subscribed(was_expired=was_exp)
                else:
                    self.plugin.set_setting("was_subscribed", False)
                    self.plugin.set_setting("was_expired_state", True)
                    self._dismiss_active_dialog()
                    self._show_expired_card()
            else:
                self._last_known_sub = cur_sub
        except Exception:
            pass

    def _start_subscription_watcher(self):
        def watcher_loop():
            import time
            from android_utils import run_on_ui_thread
            time.sleep(2.0)
            if self._stopped: return
            self._last_known_sub = self.is_subscribed()

            while not self._stopped:
                try:
                    time.sleep(2.0)
                    if self._stopped: break
                    cur_sub = self.is_subscribed()
                    prev_sub = self._last_known_sub

                    if prev_sub is not None and prev_sub != cur_sub:
                        self._last_known_sub = cur_sub
                        if cur_sub:
                            was_exp = bool(self.plugin.get_setting("was_expired_state", False))
                            self.plugin.set_setting("was_subscribed", True)
                            self.plugin.set_setting("was_expired_state", False)
                            def on_sub():
                                self._dismiss_active_dialog()
                                self._notify_subscribed(was_expired=was_exp)
                            run_on_ui_thread(on_sub)
                        else:
                            self.plugin.set_setting("was_subscribed", False)
                            self.plugin.set_setting("was_expired_state", True)
                            def on_unsub():
                                self._dismiss_active_dialog()
                                self._show_expired_card()
                            run_on_ui_thread(on_unsub)
                    else:
                        self._last_known_sub = cur_sub
                except Exception:
                    pass
        import threading
        t = threading.Thread(target=watcher_loop, daemon=True)
        t.start()

    def _check_initial_subscription_flow(self):
        def flow():
            import time
            try:
                now = time.time()
                install_time = float(self.plugin.get_setting("install_time", 0.0) or 0.0)
                if install_time <= 0:
                    install_time = now
                    self.plugin.set_setting("install_time", install_time)

                is_sub = self.is_subscribed()
                self._last_known_sub = is_sub
                was_sub = bool(self.plugin.get_setting("was_subscribed", False))
                was_exp = bool(self.plugin.get_setting("was_expired_state", False))

                if is_sub:
                    if not was_sub:
                        self.plugin.set_setting("was_subscribed", True)
                        self.plugin.set_setting("was_expired_state", False)
                        self._notify_subscribed(was_expired=was_exp)
                    return

                if was_sub or was_exp:
                    self.plugin.set_setting("was_subscribed", False)
                    self.plugin.set_setting("was_expired_state", True)
                    self._show_expired_card()
                    return

                trial_days = float(self._get_links().get("trial_days", 7))
                trial_sec = trial_days * 86400.0
                last_remind = float(self.plugin.get_setting("last_remind_time", 0.0) or 0.0)

                if (now - install_time) < trial_sec:
                    if last_remind <= 0 or (now - last_remind) >= trial_sec:
                        self._show_welcome_card()
                else:
                    self.plugin.set_setting("was_expired_state", True)
                    self._show_expired_card()
            except Exception:
                pass
        from android_utils import run_on_ui_thread
        run_on_ui_thread(flow, 1500)

    def _create_card_content(self, act, title_text, message_text):
        try:
            from android.widget import LinearLayout, TextView
            from android.view import Gravity
            from android.graphics import Typeface
            from org.telegram.messenger import AndroidUtilities, UserConfig, MediaDataController
            from org.telegram.ui.ActionBar import Theme
            from org.telegram.ui.Components import BackupImageView

            dp = AndroidUtilities.dp
            layout = LinearLayout(act)
            layout.setOrientation(LinearLayout.VERTICAL)
            layout.setGravity(Gravity.CENTER_HORIZONTAL)
            layout.setPadding(dp(24), dp(16), dp(24), dp(6))

            size = dp(76)
            iv = BackupImageView(act)
            iv.setRoundRadius(dp(18))
            lp_iv = LinearLayout.LayoutParams(size, size)
            lp_iv.gravity = Gravity.CENTER_HORIZONTAL
            lp_iv.setMargins(0, dp(4), 0, dp(16))
            iv.setLayoutParams(lp_iv)

            try:
                acc = int(UserConfig.selectedAccount)
                mdc = MediaDataController.getInstance(acc)
                raw_icon = str(self.icon_sticker)
                if "/" in raw_icon:
                    pack, idx_s = raw_icon.split("/", 1)
                    mdc.setPlaceholderImageByIndex(iv, pack, int(idx_s), "150_150")
            except Exception:
                pass
            layout.addView(iv)

            if title_text:
                tt = TextView(act)
                tt.setText(title_text)
                tt.setTextSize(19.0)
                tt.setTypeface(None, Typeface.BOLD)
                tt.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
                tt.setGravity(Gravity.CENTER_HORIZONTAL)
                lp_t = LinearLayout.LayoutParams(-1, -2)
                lp_t.setMargins(0, 0, 0, dp(12))
                tt.setLayoutParams(lp_t)
                layout.addView(tt)

            if message_text:
                mt = TextView(act)
                mt.setText(message_text)
                mt.setTextSize(15.0)
                mt.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
                mt.setLineSpacing(float(dp(3)), 1.0)
                mt.setGravity(Gravity.CENTER_HORIZONTAL)
                lp_m = LinearLayout.LayoutParams(-1, -2)
                mt.setLayoutParams(lp_m)
                layout.addView(mt)

            return layout
        except Exception:
            return None

    def _show_welcome_card(self):
        def show():
            try:
                if self._is_dialog_active(): return
                from client_utils import get_last_fragment
                frag = get_last_fragment()
                if not frag: return
                act = frag.getParentActivity()
                if not act: return

                links = self._get_links()
                url = links.get("channel_url", "https://t.me/MaxExteraPlugins")

                from ui.alert import AlertDialogBuilder
                b = AlertDialogBuilder(act)
                content = self._create_card_content(act, self.tr("install_card_title"), self.tr("install_card_msg"))
                if content is not None:
                    b.set_view(content)
                else:
                    b.set_title(self.tr("install_card_title"))
                    b.set_message(self.tr("install_card_msg"))

                def on_sub(d, w):
                    self._dismiss_active_dialog()
                    self._open_url(url)
                    def check_after():
                        if self.is_subscribed():
                            self._notify_subscribed(was_expired=False)
                    from android_utils import run_on_ui_thread
                    run_on_ui_thread(check_after, 3000)

                def on_later(d, w):
                    import time
                    self._dismiss_active_dialog()
                    self.plugin.set_setting("last_remind_time", time.time())

                b.set_positive_button(self.tr("subscribe_btn"), on_sub)
                b.set_negative_button(self.tr("remind_later_btn"), on_later)
                self._active_dialog = b.show()
            except Exception:
                pass
        from android_utils import run_on_ui_thread
        run_on_ui_thread(show)

    def _show_expired_card(self):
        def show():
            try:
                if self._is_dialog_active(): return
                from client_utils import get_last_fragment
                frag = get_last_fragment()
                if not frag: return
                act = frag.getParentActivity()
                if not act: return

                links = self._get_links()
                url = links.get("channel_url", "https://t.me/MaxExteraPlugins")

                from ui.alert import AlertDialogBuilder
                from ui.bulletin import BulletinHelper
                b = AlertDialogBuilder(act)
                content = self._create_card_content(act, self.tr("trial_expired_title"), self.tr("trial_expired_msg"))
                if content is not None:
                    b.set_view(content)
                else:
                    b.set_title(self.tr("trial_expired_title"))
                    b.set_message(self.tr("trial_expired_msg"))

                def on_sub(d, w):
                    self._dismiss_active_dialog()
                    self._open_url(url)
                    def check_after():
                        if self.is_subscribed():
                            self.plugin.set_setting("was_subscribed", True)
                            self.plugin.set_setting("was_expired_state", False)
                            self._notify_subscribed(was_expired=True)
                    from android_utils import run_on_ui_thread
                    run_on_ui_thread(check_after, 3000)

                def on_check(d, w):
                    self._dismiss_active_dialog()
                    if self.is_subscribed():
                        self.plugin.set_setting("was_subscribed", True)
                        self.plugin.set_setting("was_expired_state", False)
                        self._notify_subscribed(was_expired=True)
                    else:
                        BulletinHelper.show_error(self.tr("sub_not_found"))
                        from android_utils import run_on_ui_thread
                        run_on_ui_thread(self._show_expired_card, 500)

                b.set_positive_button(self.tr("subscribe_btn"), on_sub)
                b.set_negative_button(self.tr("check_sub_btn"), on_check)
                self._active_dialog = b.show()
            except Exception:
                pass
        from android_utils import run_on_ui_thread
        run_on_ui_thread(show)


class ReadAnyPlugin(BasePlugin):
    def on_app_event(self, event_type):
        if hasattr(self, "_author_helper"):
            self._author_helper.on_event(event_type)

    MODE_READ_SELECTED = 0
    MODE_EXCLUDE_SELECTED = 1

    def on_plugin_load(self):
        self._author_helper = AuthorChannelHelper(self, icon_sticker="MaxExteraPluginsStickers/13")
        self._author_helper.on_load()
        self._observer = None
        self._observer_registered = False
        self._injected_btn = None
        self._home_fragment_ref = None
        self._alive = True
        self._sliding_open = False
        self._inject_gen = 0

        if self.get_setting("show_in_actionbar", False):
            self._setup_actionbar_hooks()

        if self.get_setting("show_in_drawer", True):
            self._add_drawer_item()

        self.add_menu_item(
            MenuItemData(
                menu_type=MenuItemType.CHAT_ACTION_MENU,
                text="Добавить в Read Any",
                on_click=self._on_add_chat_click,
                icon="msg_markread",
                item_id="read_any_add_chat",
            )
        )

        if self.get_setting("auto_read", False):
            self._start_auto_read()

    def on_plugin_unload(self):
        if hasattr(self, "_author_helper"):
            self._author_helper.on_unload()
        self._alive = False
        self._inject_gen += 1
        self._stop_auto_read()
        self._injected_btn = None
        self._home_fragment_ref = None

    def _setup_actionbar_hooks(self):
        try:
            dialogs_clazz = find_class("org.telegram.ui.DialogsActivity")
            if dialogs_clazz:
                try:
                    self.hook_all_methods(dialogs_clazz, "createView", DialogsCreateViewHook(self))
                except Exception:
                    pass
                try:
                    self.hook_all_methods(dialogs_clazz, "onResume", DialogsResumeHook(self))
                except Exception:
                    pass
                try:
                    self.hook_all_methods(dialogs_clazz, "onBecomeFullyVisible", DialogsFullyVisibleHook(self))
                except Exception:
                    pass
        except Exception:
            pass

        try:
            rsc_clazz = find_class("org.telegram.ui.RightSlidingDialogContainer")
            if rsc_clazz:
                self.hook_all_methods(rsc_clazz, "presentFragment", SlidingPresentHook(self))
                self.hook_all_methods(rsc_clazz, "finishPreview", SlidingFinishPreviewHook(self))
        except Exception:
            pass

        self._start_inject_loop()

    def _start_inject_loop(self):
        self._inject_gen += 1
        gen = self._inject_gen
        delays = [500, 1500, 3000, 6000, 10000]
        for d in delays:
            run_on_ui_thread(lambda g=gen: self._try_inject_gen(g), d)

    def _try_inject_gen(self, gen):
        if gen != self._inject_gen or not self._alive:
            return
        self._try_inject()

    def _try_inject(self):
        if not self.get_setting("show_in_actionbar", False):
            return True
        try:
            fragment = _find_home_fragment()
            if fragment is not None:
                return self._inject_button(fragment)
        except Exception:
            pass
        return False

    def _on_sliding_opened(self):
        self._sliding_open = True
        try:
            btn = self._injected_btn
            if btn is not None:
                from android.view import View
                btn.setVisibility(View.GONE)
        except Exception:
            pass
        self._start_sliding_watcher()

    def _on_sliding_closed(self):
        self._sliding_open = False
        self._start_sliding_watcher()

    def _start_sliding_watcher(self):
        def watch():
            if not self._alive:
                return
            frag = self._home_fragment_ref
            if frag is None:
                self._sliding_open = False
                return
            if _has_sliding_fragment(frag):
                self._sliding_open = True
                try:
                    btn = self._injected_btn
                    if btn is not None:
                        from android.view import View
                        btn.setVisibility(View.GONE)
                except Exception:
                    pass
                run_on_ui_thread(watch, 300)
            else:
                self._sliding_open = False
                try:
                    btn = self._injected_btn
                    if btn is not None and self.get_setting("show_in_actionbar", False):
                        from android.view import View
                        btn.setVisibility(View.VISIBLE)
                except Exception:
                    pass

        run_on_ui_thread(watch, 350)

    def _inject_button(self, fragment):
        try:
            if not self.get_setting("show_in_actionbar", False):
                return True
            if not _is_home_dialogs(fragment):
                return False
            actionBar = fragment.getActionBar()
            if not actionBar:
                return False
            menu = actionBar.createMenu()
            if menu is None:
                return False
            existing = menu.getItem(BUTTON_ID)
            if existing is not None:
                self._injected_btn = existing
                self._home_fragment_ref = fragment
                return True
            R_drawable = jclass("org.telegram.messenger.R$drawable")
            item = menu.addItem(BUTTON_ID, R_drawable.msg_markread)
            menu.removeView(item)
            idx = max(0, menu.getChildCount() - 2)
            menu.addView(item, idx)
            item.setOnClickListener(
                OnClickListener(lambda v: self._read_selected())
            )
            self._injected_btn = item
            self._home_fragment_ref = fragment
            if self._sliding_open:
                from android.view import View
                item.setVisibility(View.GONE)
            return True
        except Exception:
            return False

    def _get_mode(self) -> int:
        return self.get_setting("read_mode", self.MODE_READ_SELECTED)

    def _is_exclude_mode(self) -> bool:
        return self._get_mode() == self.MODE_EXCLUDE_SELECTED

    @staticmethod
    def _make_key(dialog_id, topic_id=None):
        if topic_id:
            return f"{dialog_id}:{topic_id}"
        return str(dialog_id)

    @staticmethod
    def _parse_key(key):
        if ":" in key:
            parts = key.split(":", 1)
            return int(parts[0]), int(parts[1])
        return int(key), None

    def _get_selected_chats(self) -> dict:
        raw = self.get_setting("selected_chats", "{}")
        try:
            return json.loads(raw) if isinstance(raw, str) else raw
        except Exception:
            return {}

    def _save_selected_chats(self, chats: dict):
        self.set_setting("selected_chats", json.dumps(chats), reload_settings=True)

    def _add_chat(self, dialog_id: int, name: str, chat_type: str = "chat",
                  topic_id=None, topic_name: str = ""):
        chats = self._get_selected_chats()
        key = self._make_key(dialog_id, topic_id)
        entry = {"name": name, "type": chat_type}
        if topic_id:
            entry["topic_id"] = topic_id
            if topic_name:
                entry["topic_name"] = topic_name
        chats[key] = entry
        self._save_selected_chats(chats)

    def _remove_chat(self, key: str):
        chats = self._get_selected_chats()
        if key in chats:
            del chats[key]
            self._save_selected_chats(chats)

    def _is_selected(self, key: str) -> bool:
        return key in self._get_selected_chats()

    def _get_java_field(self, obj, field_name):
        try:
            clazz = obj.getClass()
            while clazz is not None:
                try:
                    field = clazz.getDeclaredField(field_name)
                    field.setAccessible(True)
                    return field.get(obj)
                except Exception:
                    clazz = clazz.getSuperclass()
        except Exception:
            pass
        return None

    def _extract_topic_info(self, context: Dict[str, Any]):
        dialog_id = context.get("dialog_id")
        fragment = context.get("fragment")
        topic_id = None
        topic_name = None

        if not dialog_id:
            chat = context.get("chat")
            user = context.get("user")
            if chat:
                dialog_id = -getattr(chat, "id", 0)
            elif user:
                dialog_id = getattr(user, "id", 0)

        if fragment is not None:
            try:
                ChatActivity = jclass("org.telegram.ui.ChatActivity")
                if isinstance(fragment, ChatActivity):
                    is_topic = getattr(fragment, "isTopic", None)
                    if is_topic is None:
                        is_topic = self._get_java_field(fragment, "isTopic")
                    if is_topic:
                        try:
                            topic_id = int(fragment.getTopicId())
                        except Exception:
                            tid = self._get_java_field(fragment, "topicId")
                            if tid:
                                topic_id = int(tid)
                        if topic_id:
                            topic_name = self._get_topic_name(dialog_id, topic_id)
            except Exception:
                pass

        return dialog_id, topic_id, topic_name

    def _get_topic_name(self, dialog_id, topic_id):
        try:
            mc = get_messages_controller()
            if mc is None:
                return None
            tc = mc.getTopicsController()
            if tc is None:
                return None
            chat_id = -dialog_id if dialog_id < 0 else dialog_id
            topic = tc.findTopic(chat_id, topic_id)
            if topic is not None:
                return getattr(topic, "title", None)
        except Exception:
            pass
        return None

    def _resolve_chat_name(self, context: Dict[str, Any]) -> str:
        chat = context.get("chat")
        if chat:
            return getattr(chat, "title", "Группа/Канал")
        user = context.get("user")
        if user:
            first = getattr(user, "first_name", "") or ""
            last = getattr(user, "last_name", "") or ""
            return f"{first} {last}".strip() or "Пользователь"
        return "Чат"

    def _resolve_chat_type(self, context: Dict[str, Any], is_topic: bool = False) -> str:
        if is_topic:
            return "topic"
        chat = context.get("chat")
        if chat:
            if getattr(chat, "forum", False):
                return "forum"
            if getattr(chat, "broadcast", False):
                return "channel"
            return "group"
        return "user"

    def _on_add_chat_click(self, context: Dict[str, Any]):
        dialog_id, topic_id, topic_name = self._extract_topic_info(context)

        if not dialog_id:
            BulletinHelper.show_error("Не удалось определить чат")
            return

        key = self._make_key(dialog_id, topic_id)

        if self._is_selected(key):
            chats = self._get_selected_chats()
            name = chats.get(key, {}).get("name", "Чат")
            self._remove_chat(key)
            BulletinHelper.show_success(f"«{name}» убран из Read Any")
            return

        chat_name = self._resolve_chat_name(context)
        is_topic = topic_id is not None
        chat_type = self._resolve_chat_type(context, is_topic)

        if is_topic:
            display_name = topic_name or f"Топик #{topic_id}"
            full_name = f"{chat_name} › {display_name}"
        else:
            full_name = chat_name

        self._add_chat(dialog_id, full_name, chat_type, topic_id, topic_name or "")
        BulletinHelper.show_success(f"«{full_name}» добавлен в Read Any")

    def _add_drawer_item(self):
        self.add_menu_item(
            MenuItemData(
                menu_type=MenuItemType.DRAWER_MENU,
                text="Прочитать выбранные",
                on_click=self._on_drawer_click,
                icon="msg_markread",
                item_id="read_any_drawer_btn",
            )
        )

    def _remove_drawer_item(self):
        self.remove_menu_item("read_any_drawer_btn")

    def _on_drawer_click(self, context: Dict[str, Any]):
        self._read_selected()

    def _create_observer(self):
        plugin = self
        NCDelegate = jclass("org.telegram.messenger.NotificationCenter$NotificationCenterDelegate")

        class Observer(dynamic_proxy(NCDelegate)):
            def __init__(self):
                super().__init__()

            def didReceivedNotification(self, notification_id, account, args):
                try:
                    NC = jclass("org.telegram.messenger.NotificationCenter")
                    if notification_id != NC.didReceiveNewMessages:
                        return
                    if args is None or len(args) < 1:
                        return
                    dialog_id = int(args[0])
                    if len(args) > 2 and args[2]:
                        return
                    plugin._auto_read_for_dialog(dialog_id)
                except Exception:
                    pass

        return Observer()

    def _start_auto_read(self):
        if self._observer_registered:
            return
        try:
            NC = jclass("org.telegram.messenger.NotificationCenter")
            self._observer = self._create_observer()
            nc = get_notification_center()
            nc.addObserver(self._observer, NC.didReceiveNewMessages)
            self._observer_registered = True
            self._read_selected_silent()
        except Exception:
            pass

    def _stop_auto_read(self):
        if not self._observer_registered or self._observer is None:
            return
        try:
            NC = jclass("org.telegram.messenger.NotificationCenter")
            nc = get_notification_center()
            nc.removeObserver(self._observer, NC.didReceiveNewMessages)
        except Exception:
            pass
        self._observer = None
        self._observer_registered = False

    def _auto_read_for_dialog(self, dialog_id):
        try:
            chats = self._get_selected_chats()
            mc = get_messages_controller()
            if mc is None:
                return

            if self._is_exclude_mode():
                self._auto_read_for_dialog_exclude(mc, dialog_id, chats)
            else:
                self._auto_read_for_dialog_include(mc, dialog_id, chats)
        except Exception:
            pass

    def _auto_read_for_dialog_include(self, mc, dialog_id, chats):
        if not chats:
            return

        did_str = str(dialog_id)

        if did_str in chats:
            info = chats[did_str]
            chat_type = info.get("type", "chat")
            if chat_type == "forum":
                run_on_ui_thread(lambda: mc.markAllTopicsAsRead(dialog_id))
            else:
                self._read_dialog_now(mc, dialog_id)
            return

        prefix = did_str + ":"
        for key, info in chats.items():
            if key.startswith(prefix):
                _, topic_id = self._parse_key(key)
                if topic_id:
                    run_on_ui_thread(
                        lambda tid=topic_id: self._read_single_topic(mc, dialog_id, tid)
                    )

    def _auto_read_for_dialog_exclude(self, mc, dialog_id, chats):
        did_str = str(dialog_id)

        if did_str in chats:
            chat_type = chats[did_str].get("type", "chat")
            if chat_type == "forum":
                return
            return

        excluded_topics = {}
        prefix = did_str + ":"
        for key in chats:
            if key.startswith(prefix):
                _, topic_id = self._parse_key(key)
                if topic_id:
                    excluded_topics[topic_id] = True

        if excluded_topics:
            run_on_ui_thread(
                lambda: self._read_forum_except_topics(mc, dialog_id, excluded_topics)
            )
        else:
            dialog = mc.dialogs_dict.get(dialog_id)
            if dialog is not None:
                is_forum = False
                try:
                    is_forum = mc.isForum(dialog_id)
                except Exception:
                    pass
                if is_forum:
                    run_on_ui_thread(lambda: mc.markAllTopicsAsRead(dialog_id))
                else:
                    self._read_dialog_now(mc, dialog_id)

    def _read_dialog_now(self, mc, dialog_id):
        def do_read():
            try:
                dialog = mc.dialogs_dict.get(dialog_id)
                if dialog is not None:
                    top_msg = getattr(dialog, "top_message", 0)
                    last_date = getattr(dialog, "last_message_date", 0)
                    mc.markMentionsAsRead(dialog_id, 0)
                    mc.markDialogAsRead(
                        dialog_id, top_msg, top_msg,
                        last_date, False, 0, 0, True, 0
                    )
            except Exception:
                pass
        run_on_ui_thread(do_read)

    def _on_auto_read_toggle(self, enabled: bool):
        if enabled:
            self._start_auto_read()
        else:
            self._stop_auto_read()

    def _read_selected_silent(self):
        if self._is_exclude_mode():
            self._read_all_except_selected_silent()
        else:
            self._read_included_silent()

    def _read_included_silent(self):
        chats = self._get_selected_chats()
        if not chats:
            return

        try:
            mc = get_messages_controller()
            if mc is None:
                return

            for key, info in chats.items():
                try:
                    did, topic_id = self._parse_key(key)
                    chat_type = info.get("type", "chat")
                    if not topic_id:
                        topic_id = info.get("topic_id")

                    if chat_type == "forum" and not topic_id:
                        try:
                            mc.markAllTopicsAsRead(did)
                            continue
                        except Exception:
                            pass

                    if chat_type == "topic" and topic_id:
                        try:
                            self._read_single_topic(mc, did, int(topic_id))
                            continue
                        except Exception:
                            try:
                                mc.markAllTopicsAsRead(did)
                                continue
                            except Exception:
                                pass

                    dialog = mc.dialogs_dict.get(did)
                    if dialog is not None:
                        top_msg = getattr(dialog, "top_message", 0)
                        last_date = getattr(dialog, "last_message_date", 0)
                        mc.markMentionsAsRead(did, 0)
                        mc.markDialogAsRead(
                            did, top_msg, top_msg,
                            last_date, False, 0, 0, True, 0
                        )
                    else:
                        mc.markDialogAsRead(
                            did, 2147483647, 2147483647,
                            0, False, 0, 0, True, 0
                        )
                        mc.markMentionsAsRead(did, 0)

                except Exception:
                    pass
        except Exception:
            pass

    def _read_all_except_selected_silent(self):
        try:
            mc = get_messages_controller()
            if mc is None:
                return

            chats = self._get_selected_chats()
            dialogs_list = mc.allDialogs

            excluded_dids = set()
            excluded_topics = {}
            for key, info in chats.items():
                did, topic_id = self._parse_key(key)
                if topic_id:
                    if did not in excluded_topics:
                        excluded_topics[did] = set()
                    excluded_topics[did].add(topic_id)
                else:
                    excluded_dids.add(did)

            for i in range(dialogs_list.size()):
                try:
                    dialog = dialogs_list.get(i)
                    did = int(dialog.id)

                    if did in excluded_dids:
                        continue

                    is_forum = False
                    try:
                        is_forum = mc.isForum(did)
                    except Exception:
                        pass

                    if is_forum and did in excluded_topics:
                        self._read_forum_except_topics(mc, did, {t: True for t in excluded_topics[did]})
                        continue

                    if is_forum:
                        mc.markAllTopicsAsRead(did)
                        continue

                    top_msg = getattr(dialog, "top_message", 0)
                    last_date = getattr(dialog, "last_message_date", 0)
                    mc.markMentionsAsRead(did, 0)
                    mc.markDialogAsRead(
                        did, top_msg, top_msg,
                        last_date, False, 0, 0, True, 0
                    )
                except Exception:
                    pass
        except Exception:
            pass

    def _read_selected(self):
        if self._is_exclude_mode():
            self._read_all_except_selected()
        else:
            self._read_included()

    def _read_included(self):
        chats = self._get_selected_chats()
        if not chats:
            return

        try:
            mc = get_messages_controller()
            if mc is None:
                BulletinHelper.show_error("MessagesController недоступен")
                return

            read_count = 0
            errors = []

            for key, info in chats.items():
                try:
                    did, topic_id = self._parse_key(key)
                    chat_type = info.get("type", "chat")
                    if not topic_id:
                        topic_id = info.get("topic_id")

                    if chat_type == "forum" and not topic_id:
                        try:
                            mc.markAllTopicsAsRead(did)
                            read_count += 1
                            continue
                        except Exception:
                            pass

                    if chat_type == "topic" and topic_id:
                        try:
                            self._read_single_topic(mc, did, int(topic_id))
                            read_count += 1
                            continue
                        except Exception:
                            try:
                                mc.markAllTopicsAsRead(did)
                                read_count += 1
                                continue
                            except Exception:
                                pass

                    dialog = mc.dialogs_dict.get(did)
                    if dialog is not None:
                        top_msg = getattr(dialog, "top_message", 0)
                        last_date = getattr(dialog, "last_message_date", 0)
                        mc.markMentionsAsRead(did, 0)
                        mc.markDialogAsRead(
                            did, top_msg, top_msg,
                            last_date, False, 0, 0, True, 0
                        )
                        read_count += 1
                    else:
                        mc.markDialogAsRead(
                            did, 2147483647, 2147483647,
                            0, False, 0, 0, True, 0
                        )
                        mc.markMentionsAsRead(did, 0)
                        read_count += 1

                except Exception:
                    name = info.get("name", key)
                    errors.append(name)

            if errors:
                run_on_ui_thread(
                    lambda: BulletinHelper.show_info(
                        f"Прочитано: {read_count}. Ошибки: {', '.join(errors)}"
                    )
                )
            else:
                run_on_ui_thread(
                    lambda: BulletinHelper.show_success(
                        f"Прочитано чатов: {read_count}"
                    )
                )

        except Exception as e:
            error_msg = str(e)
            run_on_ui_thread(
                lambda msg=error_msg: BulletinHelper.show_error(f"Ошибка: {msg}")
            )

    def _read_all_except_selected(self):
        try:
            mc = get_messages_controller()
            if mc is None:
                BulletinHelper.show_error("MessagesController недоступен")
                return

            chats = self._get_selected_chats()
            dialogs_list = mc.allDialogs

            excluded_dids = set()
            excluded_topics = {}
            for key, info in chats.items():
                did, topic_id = self._parse_key(key)
                if topic_id:
                    if did not in excluded_topics:
                        excluded_topics[did] = set()
                    excluded_topics[did].add(topic_id)
                else:
                    excluded_dids.add(did)

            read_count = 0
            errors = []

            for i in range(dialogs_list.size()):
                try:
                    dialog = dialogs_list.get(i)
                    did = int(dialog.id)

                    if did in excluded_dids:
                        continue

                    is_forum = False
                    try:
                        is_forum = mc.isForum(did)
                    except Exception:
                        pass

                    if is_forum and did in excluded_topics:
                        self._read_forum_except_topics(mc, did, {t: True for t in excluded_topics[did]})
                        read_count += 1
                        continue

                    if is_forum:
                        mc.markAllTopicsAsRead(did)
                        read_count += 1
                        continue

                    top_msg = getattr(dialog, "top_message", 0)
                    last_date = getattr(dialog, "last_message_date", 0)
                    mc.markMentionsAsRead(did, 0)
                    mc.markDialogAsRead(
                        did, top_msg, top_msg,
                        last_date, False, 0, 0, True, 0
                    )
                    read_count += 1
                except Exception:
                    errors.append(str(i))

            if errors:
                run_on_ui_thread(
                    lambda: BulletinHelper.show_info(
                        f"Прочитано: {read_count}. Ошибки: {len(errors)}"
                    )
                )
            else:
                run_on_ui_thread(
                    lambda: BulletinHelper.show_success(
                        f"Прочитано чатов: {read_count}"
                    )
                )

        except Exception as e:
            error_msg = str(e)
            run_on_ui_thread(
                lambda msg=error_msg: BulletinHelper.show_error(f"Ошибка: {msg}")
            )

    def _read_forum_except_topics(self, mc, dialog_id, excluded_topics_map):
        try:
            chat_id = -dialog_id if dialog_id < 0 else dialog_id
            tc = mc.getTopicsController()
            if tc is None:
                return

            topics = tc.getTopics(chat_id)
            if topics is None:
                return

            is_mono = False
            try:
                is_mono = mc.isMonoForum(dialog_id)
            except Exception:
                pass

            DialogObject = jclass("org.telegram.messenger.DialogObject")
            ms = get_messages_storage()

            for i in range(topics.size()):
                try:
                    topic = topics.get(i)
                    tid = getattr(topic, "id", 0)

                    if tid in excluded_topics_map:
                        continue

                    top_msg = getattr(topic, "top_message", 0)
                    top_message_obj = getattr(topic, "topMessage", None)
                    msg_date = getattr(top_message_obj, "date", 0) if top_message_obj else 0

                    if is_mono:
                        read_topic_id = DialogObject.getPeerDialogId(topic.from_id)
                    else:
                        read_topic_id = tid

                    mc.markDialogAsRead(
                        dialog_id, top_msg, 0,
                        msg_date, False, read_topic_id, 0, True, 0
                    )

                    if ms:
                        ms.updateRepliesMaxReadId(
                            chat_id, read_topic_id, top_msg, 0, True
                        )
                except Exception:
                    pass
        except Exception:
            pass

    def _read_single_topic(self, mc, dialog_id, topic_id):
        chat_id = -dialog_id if dialog_id < 0 else dialog_id
        tc = mc.getTopicsController()
        topic = tc.findTopic(chat_id, topic_id) if tc else None

        if topic is not None:
            top_msg = getattr(topic, "top_message", 0)
            top_message_obj = getattr(topic, "topMessage", None)
            msg_date = getattr(top_message_obj, "date", 0) if top_message_obj else 0

            is_mono = False
            try:
                is_mono = mc.isMonoForum(dialog_id)
            except Exception:
                pass

            if is_mono:
                DialogObject = jclass("org.telegram.messenger.DialogObject")
                read_topic_id = DialogObject.getPeerDialogId(topic.from_id)
            else:
                read_topic_id = topic_id

            mc.markDialogAsRead(
                dialog_id, top_msg, 0,
                msg_date, False, read_topic_id, 0, True, 0
            )

            ms = get_messages_storage()
            if ms:
                ms.updateRepliesMaxReadId(
                    chat_id, read_topic_id, top_msg, 0, True
                )
        else:
            mc.markDialogAsRead(
                dialog_id, 2147483647, 0,
                0, False, topic_id, 0, True, 0
            )

    def _on_drawer_toggle(self, enabled: bool):
        if enabled:
            self._add_drawer_item()
        else:
            self._remove_drawer_item()

    def _on_read_selected_click(self, view):
        self._read_selected()

    def _make_remove_handler(self, key, name):
        def handler(view):
            self._remove_chat(key)
            BulletinHelper.show_success(f"«{name}» убран из списка")
        return handler

    def _on_mode_change(self, new_index: int):
        pass

    def create_settings(self):
        try:
            items = self._inner_create_settings()
        except Exception:
            items = []
        if hasattr(self, '_author_helper'):
            return self._author_helper.prepend_settings(items)
        return items

    def _inner_create_settings(self):
        items = []

        items.append(Header(text="Действия"))
        items.append(
            Text(
                text="Прочитать выбранные",
                icon="msg_markread",
                on_click=self._on_read_selected_click,
            )
        )
        items.append(Divider())

        items.append(Header(text="Авточтение"))
        items.append(
            Switch(
                key="auto_read",
                text="Авто-прочтение",
                default=False,
                subtext="При включении новые сообщения в выбранных чатах будут автоматически помечаться как прочитанные",
                icon="msg_retry",
                on_change=self._on_auto_read_toggle,
            )
        )
        items.append(Divider())

        items.append(Header(text="Отображение кнопки прочтения"))
        items.append(
            Switch(
                key="show_in_drawer",
                text="Боковое меню",
                default=True,
                icon="msg_menu",
                on_change=self._on_drawer_toggle,
            )
        )
        items.append(
            Switch(
                key="show_in_actionbar",
                text="Главный экран",
                default=False,
                subtext="Требуется перезагрузка плагина при включении",
                icon="msg_header",
            )
        )
        items.append(Divider())

        chats = self._get_selected_chats()
        mode = self._get_mode()

        if mode == self.MODE_EXCLUDE_SELECTED:
            header_label = f"Исключённые чаты ({len(chats)})"
        else:
            header_label = f"Выбранные чаты ({len(chats)})"

        items.append(Header(text=header_label))

        items.append(
            Selector(
                key="read_mode",
                text="Режим работы",
                default=self.MODE_READ_SELECTED,
                items=["Прочитать выбранные", "Исключить выбранные"],
                icon="msg_customize",
                on_change=self._on_mode_change,
            )
        )

        if chats:
            type_icons = {
                "user": "msg_contacts",
                "group": "msg_groups",
                "channel": "msg_channel",
                "forum": "msg_discussion",
                "topic": "msg_topic_create",
            }
            type_labels = {
                "user": "Личные сообщения",
                "group": "Группа",
                "channel": "Канал",
                "forum": "Форум (все топики)",
                "topic": "Топик форума",
            }

            for key, info in chats.items():
                name = info.get("name", f"Чат {key}")
                chat_type = info.get("type", "chat")
                icon = type_icons.get(chat_type, "msg_discussion")
                label = type_labels.get(chat_type, "Чат")

                items.append(
                    Text(
                        text=name,
                        subtext=f"{label} • Нажмите чтобы удалить",
                        icon=icon,
                        red=False,
                        on_click=self._make_remove_handler(key, name),
                    )
                )

        if mode == self.MODE_EXCLUDE_SELECTED:
            items.append(Divider(text="Будут прочитаны ВСЕ чаты кроме указанных выше. Добавляйте исключения через меню (⋮) внутри нужного чата или топика"))
        else:
            items.append(Divider(text="Добавляйте чаты через меню (⋮) внутри нужного чата или топика"))

        if hasattr(self, "_author_helper"):


            return self._author_helper.prepend_settings(items)


        return items
