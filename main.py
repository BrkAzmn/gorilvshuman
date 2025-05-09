import streamlit as st
import random
import pandas as pd
import matplotlib.pyplot as plt


class Human:
    def __init__(self, weapon='none'):
        self.health = 10
        self.alive = True
        self.weapon = weapon
        self.base_strength = 6
        self.strength = self.assign_strength(weapon)
        self.crit_chance = self.assign_crit(weapon)

    def assign_strength(self, weapon):
        return {
            'stick': self.base_strength * 1.25,
            'stone': self.base_strength * 0.75,
            'knife': self.base_strength * 1.5,
        }.get(weapon, self.base_strength)

    def assign_crit(self, weapon):
        return {'knife': 0.15}.get(weapon, 0.02)

    def attack(self):
        if not self.alive:
            return 0
        damage = self.strength
        if random.random() < self.crit_chance:
            damage *= 2
        return damage

    def receive_damage(self, dmg):
        self.health -= dmg
        if self.health <= 0:
            self.alive = False
            return True
        return False


class Gorilla:
    def __init__(self):
        self.health = 1000
        self.strength = 100
        self.stamina = 100
        self.aggression = 1.0
        self.aggressive_mode = False

    def attack(self, humans, initial=False):
        hits = 3 if initial else min(3, len(humans))
        casualties = 0
        for _ in range(hits):
            target = random.choice(humans)
            if target.alive:
                died = target.receive_damage(self.strength * self.aggression)
                if died:
                    casualties += 1
        return casualties

    def receive_damage(self, dmg):
        self.health -= dmg
        if self.health < 25 and not self.aggressive_mode:
            self.aggression = 1.5
            self.aggressive_mode = True

    def fatigue(self):
        self.stamina -= 2
        if self.stamina < 0:
            self.strength *= 0.95

def simulate_battle(num_humans, weapon_dist, coordination, sim_count):
    results = []
    for _ in range(sim_count):
        humans = []
        weapons = sum([[k] * v for k, v in weapon_dist.items()], [])
        for i in range(num_humans):
            weapon = weapons[i] if i < len(weapons) else 'none'
            humans.append(Human(weapon))

        goril = Gorilla()
        morale = 80
        casualties = 0
        rounds = 0
        morale_log, stamina_log, alive_log = [], [], []

        initial_kills = goril.attack(humans, initial=True)
        casualties += initial_kills
        morale -= 5 * initial_kills

        while any(h.alive for h in humans) and goril.health > 0:
            rounds += 1
            attackers = [h for h in humans if h.alive]
            num_attackers = int(len(attackers) * coordination)
            total_damage = sum(h.attack() for h in attackers[:num_attackers])
            goril.receive_damage(total_damage)

            alive_humans = [h for h in humans if h.alive]
            round_kills = goril.attack(alive_humans)
            casualties += round_kills
            morale -= round_kills * 2

            if morale < 30 and casualties > 5:
                coordination *= 0.8

            goril.fatigue()
            morale_log.append(max(morale, 0))
            stamina_log.append(max(goril.stamina, 0))
            alive_log.append(sum(h.alive for h in humans))

            if morale <= 0:
                break

        results.append({
            'gorilla_health': goril.health,
            'human_casualties': casualties,
            'rounds': rounds,
            'gorilla_alive': goril.health > 0,
            'morale_log': morale_log,
            'stamina_log': stamina_log,
            'alive_log': alive_log,
        })
    return results

st.set_page_config(page_title="Goril vs İnsanlar", layout="wide")
st.title("🦍 Gümüş Sırtlı Goril vs İnsanlar Simülasyonu")

st.markdown("Bu simülasyon, bilimsel verilere dayalı olarak 1 goril ile bir grup insanın savaşını modellemektedir. "
            "Moral, yorgunluk, silah çeşitliliği ve takım koordinasyonu gibi faktörler dikkate alınır.(1 tur ortalama 2 dakikadan oluşur)")

num_humans = st.slider("👥 İnsan Sayısı", 10, 150, 100)
coordination = st.slider("🤝 Koordinasyon (0: Dağınık, 1: Uyumlu)", 0.1, 1.0, 0.6)
sim_count = st.slider("🔁 Simülasyon Sayısı", 1, 1000, 300)

st.markdown("### 🧰 Silah Dağılımı (Kişi sayısını aşmamalı)")
stick = st.number_input("Sopa", 0, num_humans, 0)
stone = st.number_input("Taş", 0, num_humans, 0)
knife = st.number_input("Bıçak", 0, num_humans, 0)
none = max(num_humans - (stick + stone + knife), 0)
weapon_dist = {'stick': stick, 'stone': stone, 'knife': knife, 'none': none}

if stick + stone + knife > num_humans:
    st.error("⚠️ Silah sayısı toplam insan sayısını geçemez!")
else:
    if st.button("🚀 Simülasyonu Başlat"):
        results = simulate_battle(num_humans, weapon_dist, coordination, sim_count)
        st.success("Simülasyon tamamlandı ✅")


        goril_wins = sum(1 for r in results if r['gorilla_alive'])
        insan_wins = sim_count - goril_wins
        avg_kayip = sum(r['human_casualties'] for r in results) / sim_count
        avg_tur = sum(r['rounds'] for r in results) / sim_count

        col1, col2, col3 = st.columns(3)
        col1.metric("🦍 Goril Kazanma Sayısı", goril_wins)
        col2.metric("🧍 İnsan Kazanma Sayısı", insan_wins)
        col3.metric("💀 Ortalama Kayıp", f"{avg_kayip:.2f}")


        st.markdown("###  Göre Ortalama Moral Seviyesi")
        df_moral = pd.DataFrame([r['morale_log'] for r in results])
        df_moral.mean().plot(title="Ortalama Moral Seviyesi")
        plt.xlabel("Tur")
        plt.ylabel("Moral Puanı")
        st.pyplot(plt.gcf())
        plt.clf()

        st.markdown("### 🔋 Goril Yorgunluk (Stamina) Düşüş Seviyesi")
        df_stamina = pd.DataFrame([r['stamina_log'] for r in results])
        df_stamina.mean().plot(title="Ortalama Goril Stamina")
        plt.xlabel("Tur")
        plt.ylabel("Stamina")
        st.pyplot(plt.gcf())
        plt.clf()

        st.markdown("### 👥 Tura Göre Hayatta Kalan İnsan Sayısı")
        df_alive = pd.DataFrame([r['alive_log'] for r in results])
        df_alive.mean().plot(title="Ortalama Canlı İnsan")
        plt.xlabel("Tur")
        plt.ylabel("Canlı Sayısı")
        st.pyplot(plt.gcf())
        plt.clf()

        st.markdown("### 📊 İlk 10 Tur İçin Moral ve Yorgunluk Tablosu")
        st.dataframe(pd.DataFrame({
            'Moral': df_moral.mean().round(2),
            'Stamina': df_stamina.mean().round(2),
            'Hayatta Kalan': df_alive.mean().round(2)
        }).head(10))




