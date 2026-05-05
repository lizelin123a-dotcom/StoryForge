from enum import Enum


class Emotion(str, Enum):
    CURIOSITY = "好奇"
    TENSION = "紧张"
    SUFFOCATED = "憋屈"
    SATISFACTION_BURST = "爽"
    SATISFIED = "满足"
    EXPECTATION = "期待"
    SHOCK = "震撼"
    ANGER = "愤怒"
    ANXIETY = "焦虑"
    AFTERTASTE = "回味"
