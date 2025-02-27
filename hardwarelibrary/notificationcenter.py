
class Notification:
    def __init__(self, name, object=None, userInfo=None):
        self.name = name
        self.object = object
        self.userInfo = userInfo

class ObserverInfo:
    def __init__(self, observer, method=None, notificationName=None, observedObject=None):
        self.observer = observer
        self.method = method
        self.observedObject = observedObject
        self.notificationName = notificationName

    def matches(self, otherObserver) -> bool:
        if self.notificationName is not None and otherObserver.notificationName is not None and self.notificationName != otherObserver.notificationName:
            return False
        elif self.observedObject is not None and otherObserver.observedObject is not None and self.observedObject != otherObserver.observedObject:
            return False
        elif self.observer != otherObserver.observer:
            return False
        return True

    def __eq__(self, rhs):
        return self.matches(rhs)

class NotificationCenter:
    _instance = None
    def __init__(self):
        if not hasattr(self, 'observers'):
            self.observers = {}

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

    def addObserver(self, observer, method, notificationName, observedObject=None):
        observerInfo = ObserverInfo(observer=observer, method=method, notificationName=notificationName, observedObject=observedObject)

        if notificationName not in self.observers.keys():
            self.observers[notificationName] = [observerInfo]
        else:
            if observerInfo not in self.observers[notificationName]:
                self.observers[notificationName].append(observerInfo)

    def removeObserver(self, observer, notificationName=None, observedObject=None):
        observerToRemove = ObserverInfo(observer=observer, notificationName=notificationName, observedObject=observedObject)

        if notificationName is not None:
            self.observers[notificationName] = [currentObserver for currentObserver in self.observers[notificationName] if not currentObserver.matches(observerToRemove) ]
        else:
            for name in self.observers.keys():
                self.observers[name] = [observer for observer in self.observers[name] if not observer.matches(observerToRemove) ]        

    def postNotification(self, notificationName, notifyingObject, userInfo=None):
        if notificationName in self.observers.keys():
            notification = Notification(notificationName, notifyingObject, userInfo)
            for observerInfo in self.observers[notificationName]:
                if observerInfo.observedObject is None or observerInfo.observedObject == notifyingObject:
                    observerInfo.method(notification)

    def observersCount(self):
        count = 0
        for name in self.observers.keys():
            count += len(self.observers[name])
        return count

    def clear(self):
        self.observers = {}
