"""Native AppKit status item and opt-in UserNotifications; called on the UI thread."""
import uuid
_TARGET=None

class MacDesktop:
    def __init__(self,icon_path,enqueue):
        import AppKit
        import Foundation
        global _TARGET
        if _TARGET is None:
            class AutoTyperStatusTarget(Foundation.NSObject):
                def invoke_(self,sender):self.enqueue(str(sender.representedObject()))
            _TARGET=AutoTyperStatusTarget
        self.appkit=AppKit;self.target=_TARGET.alloc().init();self.target.enqueue=enqueue
        self.status_item=None;self.ready=False;self.center=None
    def start(self):
        kit=self.appkit
        self.status_item=kit.NSStatusBar.systemStatusBar().statusItemWithLength_(kit.NSVariableStatusItemLength)
        image=kit.NSImage.imageWithSystemSymbolName_accessibilityDescription_('keyboard','AutoTyper Pro')
        self.status_item.button().setImage_(image);self.status_item.button().setToolTip_('AutoTyper Pro')
        self.ready=True;return True
    def update(self,status,labels):
        kit=self.appkit;menu=kit.NSMenu.alloc().initWithTitle_('AutoTyper Pro')
        state=kit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('AutoTyper Pro · '+status,None,'');state.setEnabled_(False);menu.addItem_(state)
        menu.addItem_(kit.NSMenuItem.separatorItem())
        for command,label in labels.items():
            if command in ('stop_all','settings','quit'):menu.addItem_(kit.NSMenuItem.separatorItem())
            item=kit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(label,'invoke:','')
            item.setTarget_(self.target);item.setRepresentedObject_(command);menu.addItem_(item)
        self.status_item.setMenu_(menu)
    def _notifications(self):
        if self.center is None:
            import UserNotifications
            self.center=UserNotifications.UNUserNotificationCenter.currentNotificationCenter()
        return self.center
    def request_notifications(self,callback):
        import UserNotifications as un
        self._notifications().requestAuthorizationWithOptions_completionHandler_(un.UNAuthorizationOptionAlert|un.UNAuthorizationOptionSound,lambda granted,error:callback(bool(granted and error is None)))
    def notify(self,title,message):
        import UserNotifications as un
        content=un.UNMutableNotificationContent.alloc().init();content.setTitle_(title);content.setBody_(message)
        request=un.UNNotificationRequest.requestWithIdentifier_content_trigger_('autotyper-'+str(uuid.uuid4()),content,None)
        self._notifications().addNotificationRequest_withCompletionHandler_(request,None);return True
    def stop(self):
        self.ready=False
        if self.status_item is not None:
            self.appkit.NSStatusBar.systemStatusBar().removeStatusItem_(self.status_item);self.status_item=None
        self.target.enqueue=lambda command:None
