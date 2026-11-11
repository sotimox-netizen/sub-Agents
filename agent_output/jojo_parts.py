# -*- coding: utf-8 -*-
"""Выводит список частей JoJo's Bizarre Adventure с датами выхода (манга)."""

parts = [
    ("Phantom Blood", 1987),
    ("Battle Tendency", 1987),
    ("Stardust Crusaders", 1989),
    ("Diamond is Unbreakable", 1992),
    ("Golden Wind", 1995),
    ("Stone Ocean", 2000),
    ("Steel Ball Run", 2004),
    ("JoJolion", 2011),
    ("The JOJOLands", 2023),
]

print("Части JoJo's Bizarre Adventure (манга):")
for i, (name, year) in enumerate(parts, start=1):
    print(f"{i}. {name} — {year}")
