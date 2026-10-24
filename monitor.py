import asyncio
import re
import tkinter as tk

try:
    from winrt.windows.ui.notifications import KnownNotificationBindings, NotificationKinds
    from winrt.windows.ui.notifications.management import (
        UserNotificationListener,
        UserNotificationListenerAccessStatus,
    )
except ImportError:
    KnownNotificationBindings = None
    NotificationKinds = None
    UserNotificationListener = None
    UserNotificationListenerAccessStatus = None

COLORS = {
    "page": "#F4F7FA",
    "surface": "#FFFFFF",
    "ink": "#15263B",
    "muted": "#52657A",
    "navy": "#173B63",
    "teal": "#147D78",
    "line": "#D8E1E9",
    "soft_blue": "#EAF0F5",
    "soft_green": "#E1F3EE",
    "green": "#126C59",
    "soft_amber": "#FFF1E6",
    "amber": "#8B4A10",
    "soft_red": "#FCE8E8",
    "red": "#9B2C2C",
}

LINK_PATTERN = re.compile(
    r"(https?://|www\.|\b[a-z0-9-]+\.(com|net|org|info|biz|co|ru)\b)",
    re.IGNORECASE,
)

WARNING_PHRASES = {
    "pressure": (
        "urgent",
        "immediately",
        "act now",
        "final warning",
        "within 24 hours",
        "account will be closed",
        "suspended",
        "locked",
    ),
    "account request": (
        "verify your account",
        "confirm your identity",
        "reset your password",
        "update your account",
        "sign in",
        "security code",
        "verification code",
        "one-time code",
        "password",
    ),
    "payment request": (
        "gift card",
        "itunes",
        "target card",
        "wire transfer",
        "bitcoin",
        "cryptocurrency",
        "crypto",
        "zelle",
        "moneygram",
        "processing fee",
        "payment required",
        "pay now",
    ),
    "threat": (
        "arrest",
        "warrant",
        "police",
        "lawsuit",
        "legal action",
        "will be deactivated",
    ),
    "secrecy": (
        "keep this secret",
        "don't tell",
        "do not tell",
        "stay quiet",
        "don't call",
    ),
    "official identity": (
        "social security",
        "medicare",
        "internal revenue service",
        "irs",
        "your bank",
        "microsoft support",
    ),
}


def find_warning_signals(message):
    text = str(message or "")
    lowered = text.casefold()
    found = {
        label
        for label, phrases in WARNING_PHRASES.items()
        if any(phrase in lowered for phrase in phrases)
    }

    if LINK_PATTERN.search(text):
        found.add("link")

    return found


def looks_high_risk(signals):
    linked_request = "link" in signals and "account request" in signals
    pressured_account = (
        "account request" in signals
        and ("pressure" in signals or "threat" in signals)
    )
    pressured_payment = (
        "payment request" in signals
        and ("pressure" in signals or "threat" in signals or "secrecy" in signals)
    )
    impersonation = (
        "official identity" in signals
        and ("payment request" in signals or "threat" in signals)
        and ("pressure" in signals or "account request" in signals)
    )

    return linked_request or pressured_account or pressured_payment or impersonation


def read_notification(notification_item):
    source = "An app"
    try:
        display_name = notification_item.app_info.display_info.display_name
        if display_name:
            source = str(display_name).strip()
    except Exception:
        pass

    message_parts = []
    try:
        binding = notification_item.notification.visual.get_binding(
            KnownNotificationBindings.TOAST_GENERIC
        )
        if binding:
            message_parts = [
                str(element.text).strip()
                for element in binding.get_text_elements()
                if element.text and str(element.text).strip()
            ]
    except Exception:
        pass

    return source, " ".join(message_parts)


def show_scam_alert(source, signals):
    reasons = ", ".join(sorted(signals))
    message = (
        f"{source}: {reasons}. Verify the request through a trusted source."
    )

    try:
        from plyer import notification as desktop_notification

        desktop_notification.notify(
            title="ScamShield found a suspicious notification",
            message=message,
            app_name="ScamShield",
            timeout=12,
        )
    except Exception:
        print(f"ScamShield alert: {message}")


class NotificationMonitor:
    def __init__(self, root):
        self.root = root
        self.loop = asyncio.new_event_loop()
        self.monitor_task = None
        self.is_closing = False

        self.status = tk.StringVar(value="Not monitoring")
        self.detail = tk.StringVar(
            value="Start monitoring to check new Windows notifications."
        )

        self.build_window()
        self.root.after(15, self.pump_asyncio)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def build_window(self):
        self.root.title("ScamShield Notification Protection")
        self.root.geometry("660x500")
        self.root.minsize(600, 460)
        self.root.configure(background=COLORS["page"])

        accent = tk.Frame(self.root, background=COLORS["teal"], height=5)
        accent.pack(fill="x")
        accent.pack_propagate(False)

        header = tk.Frame(
            self.root,
            background=COLORS["navy"],
            padx=30,
            pady=24,
        )
        header.pack(fill="x")

        tk.Label(
            header,
            text="ScamShield",
            font=("Segoe UI", 23, "bold"),
            foreground=COLORS["surface"],
            background=COLORS["navy"],
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Windows notification protection",
            font=("Segoe UI", 13),
            foreground="#E4EDF6",
            background=COLORS["navy"],
        ).pack(anchor="w", pady=(5, 0))

        content = tk.Frame(
            self.root,
            background=COLORS["page"],
            padx=28,
            pady=24,
        )
        content.pack(fill="both", expand=True)

        status_card = tk.Frame(
            content,
            background=COLORS["surface"],
            highlightbackground=COLORS["line"],
            highlightthickness=1,
            padx=22,
            pady=20,
        )
        status_card.pack(fill="x")

        tk.Label(
            status_card,
            text="Monitor status",
            font=("Segoe UI", 13, "bold"),
            foreground=COLORS["muted"],
            background=COLORS["surface"],
        ).pack(anchor="w")

        self.status_label = tk.Label(
            status_card,
            textvariable=self.status,
            font=("Segoe UI", 18, "bold"),
            foreground=COLORS["navy"],
            background=COLORS["soft_blue"],
            padx=12,
            pady=7,
        )
        self.status_label.pack(anchor="w", pady=(12, 10))

        tk.Label(
            status_card,
            textvariable=self.detail,
            font=("Segoe UI", 12),
            foreground=COLORS["ink"],
            background=COLORS["surface"],
            justify="left",
            wraplength=540,
        ).pack(anchor="w", pady=(0, 18))

        buttons = tk.Frame(status_card, background=COLORS["surface"])
        buttons.pack(anchor="w")

        self.start_button = tk.Button(
            buttons,
            text="Start monitoring",
            command=self.start,
            font=("Segoe UI", 12, "bold"),
            foreground=COLORS["surface"],
            background=COLORS["navy"],
            activeforeground=COLORS["surface"],
            activebackground="#22517F",
            disabledforeground="#E4EDF6",
            disabledbackground="#7D91A6",
            relief="flat",
            padx=18,
            pady=10,
            cursor="hand2",
            takefocus=True,
        )
        self.start_button.pack(side="left")

        self.stop_button = tk.Button(
            buttons,
            text="Stop",
            command=self.stop,
            font=("Segoe UI", 12, "bold"),
            foreground=COLORS["navy"],
            background=COLORS["surface"],
            activeforeground=COLORS["navy"],
            activebackground=COLORS["soft_blue"],
            relief="solid",
            bd=1,
            padx=18,
            pady=9,
            cursor="hand2",
            takefocus=True,
            state="disabled",
        )
        self.stop_button.pack(side="left", padx=(10, 0))

        privacy_card = tk.Frame(
            content,
            background=COLORS["surface"],
            highlightbackground=COLORS["line"],
            highlightthickness=1,
            padx=18,
            pady=14,
        )
        privacy_card.pack(fill="x", pady=(16, 0))

        tk.Label(
            privacy_card,
            text="Privacy and limits",
            font=("Segoe UI", 12, "bold"),
            foreground=COLORS["navy"],
            background=COLORS["surface"],
        ).pack(anchor="w")

        tk.Label(
            privacy_card,
            text=(
                "Notification text is checked on this computer. ScamShield alerts "
                "only when several warning signs appear together. A quiet result "
                "does not prove a message is safe."
            ),
            font=("Segoe UI", 11),
            foreground=COLORS["muted"],
            background=COLORS["surface"],
            justify="left",
            wraplength=550,
        ).pack(anchor="w", pady=(5, 0))

    def set_status(self, text, detail, tone="neutral"):
        tones = {
            "neutral": (COLORS["soft_blue"], COLORS["navy"]),
            "active": (COLORS["soft_green"], COLORS["green"]),
            "warning": (COLORS["soft_amber"], COLORS["amber"]),
            "error": (COLORS["soft_red"], COLORS["red"]),
        }
        background, foreground = tones[tone]
        self.status.set(text)
        self.detail.set(detail)
        self.status_label.configure(
            background=background,
            foreground=foreground,
        )

    def pump_asyncio(self):
        if self.is_closing:
            return

        self.loop.call_soon(self.loop.stop)
        self.loop.run_forever()
        self.root.after(15, self.pump_asyncio)

    def start(self):
        if UserNotificationListener is None:
            self.set_status(
                "Setup needed",
                "Install the Windows notification packages from requirements.txt, "
                "then reopen ScamShield.",
                "warning",
            )
            return

        if self.monitor_task and not self.monitor_task.done():
            return

        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.set_status(
            "Requesting Windows access",
            "Windows may ask whether ScamShield can read notifications.",
        )
        self.monitor_task = self.loop.create_task(self.watch_notifications())

    def stop(self):
        if self.monitor_task and not self.monitor_task.done():
            self.monitor_task.cancel()

        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.set_status(
            "Not monitoring",
            "Start monitoring whenever you are ready.",
        )

    async def watch_notifications(self):
        try:
            listener = UserNotificationListener.current
            access = listener.get_access_status()

            if access == UserNotificationListenerAccessStatus.UNSPECIFIED:
                access = await listener.request_access_async()

            if access != UserNotificationListenerAccessStatus.ALLOWED:
                self.set_status(
                    "Access not granted",
                    "Notification access is required. You can change this later "
                    "in Windows privacy settings.",
                    "warning",
                )
                return

            current = await listener.get_notifications_async(NotificationKinds.TOAST)
            seen_ids = {item.id for item in current}

            self.set_status(
                "Monitoring",
                "ScamShield is checking new notifications. Keep this window open "
                "while monitoring is on.",
                "active",
            )

            while True:
                current = await listener.get_notifications_async(NotificationKinds.TOAST)

                for item in current:
                    if item.id in seen_ids:
                        continue

                    seen_ids.add(item.id)
                    source, message = read_notification(item)

                    if source.casefold().startswith("scamshield") or not message:
                        continue

                    signals = find_warning_signals(message)
                    if looks_high_risk(signals):
                        show_scam_alert(source, signals)

                current_ids = {item.id for item in current}
                seen_ids.intersection_update(current_ids)
                await asyncio.sleep(2)

        except asyncio.CancelledError:
            return
        except Exception:
            self.set_status(
                "Windows setup is required",
                "Windows could not start notification monitoring. This feature "
                "needs an installed app package with notification-listener access "
                "and permission from Windows.",
                "error",
            )
        finally:
            if not self.is_closing:
                self.start_button.configure(state="normal")
                self.stop_button.configure(state="disabled")

    def close(self):
        self.is_closing = True

        if self.monitor_task and not self.monitor_task.done():
            self.monitor_task.cancel()
            self.loop.run_until_complete(
                asyncio.gather(self.monitor_task, return_exceptions=True)
            )

        self.loop.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    NotificationMonitor(root)
    root.mainloop()


if __name__ == "__main__":
    main()