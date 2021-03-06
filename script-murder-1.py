#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 28 22:15:32 2018
Version 3.2.1
@author: Emmanuel Peyronnet (AzurQ)

"""

# Modules importés
import numpy as np
from math import exp
from math import e
from math import log
from math import sqrt
from math import ceil
from random import random
import time
import pickle



# Classe pour renvoyer des erreurs
class erreur(Exception):
    def __init__(self, message):
        self.message = message



# Classe vampire pour les PJs
class vampire:
    def __init__(self, nom, ps, ps0, pa, groupe, classe, generation, rang,
                 vitalite, valeur_attaque, initiative,
                 infecte, date_infection, date_mort, force_infection,
                 stun, stun_raison, etourdi, etourdi_tour, lien, maudit, date_reveil, fuite):
        self.nom = nom
        self.ps0 = ps0
        # ps0 est la valeur initiale de ps
        self.ps = ps
        self.pa = pa
        self.groupe = groupe
        # Groupe Sanguin
        self.classe = classe
        # La classe est le type vampirique parmi (1,2,4,0,0.5) :
        # 1 et 2 sont les classes I et II
        # 4 sont les vampire élémentaires (4 éléments)
        # 0 sont les vampires originels
        # 0.5 sont les demi-vampires
        self.generation = generation
        self.rang = rang
        # La génération est la génération réelle, le rang est la génération
        # apparente, pas par abus de language mais pour avoir un terme différent
        self.vitalite = vitalite
        self.valeur_attaque = valeur_attaque
        self.initiative = initiative
        self.infecte = infecte
        # Booléen indiquant si le personnage est infecté par la molécule
        self.date_infection = date_infection
        # Moment précis de la contamination
        self.date_mort = date_mort
        # Heure à laquelle le personnage mourra du virus
        self.force_infection = force_infection
        # 1 (Molécule standard) ou 2 (Dose concentrée)
        self.stun = stun
        # Représente le nombre de tours où le personnage sera immobilisé
        self.stun_raison = stun_raison
        # Donne la raison pour laquelle le personnage est immobilisé
        self.etourdi = etourdi
        # Donne la probabilité de rester étourdi à chaque tour
        # Indépendant du stun car fonctionne sur une mécanique différente
        self.etourdi_tour = etourdi_tour
        # Booléan indiquant si le personnage vient d'être étourdi ce tour
        self.lien = lien
        # Représente le nombre de PS de liens de sang que le personnage subit
            # en restriction à cause du pouvoir de Crowe (Pharacibr)
        self.maudit = maudit
        # Booléan indiquant sile joueur a utilisé la Lance
        self.date_reveil = date_reveil
        # Représente l'heure à laquelle un joueur transpercé par la Lance ressuscitera
        self.fuite = fuite
        # Indique le nombre de tours pour que le personnage puisse fuire


    # Porter une attaque à un autre joueur
    def attaque(self, cible, classe = None, surprise = False, nombre = 1):
        # Le vampire attaquant doit faire une prédiction du type vampire de sa cible
        # La classe est la prédiction de l'attaquant sur la classe de sa cible
        # Il faut entrer le nombre correspond à la classe
        # Un vampire défendant n'a cependant pas cette obligation et il n'y a
            # pas besoin de préciser cet argument qui est est nul par défaut

        # Surprise permet de préciser si le vampire attaquant a un avantage
            # de type surprise, stratégique ou autre ...
        # Cela pourra modifier sa valeur d'avantage ou désavantage.
        # En fonction de son éventuelle prédiction, il peut également avoir un désavantage
        # Avantage peut être +1, -1 ou revenir à 0

        # Dressmond ne peut pas faire plusieurs attaques
        if isinstance(self, dressmond) and nombre > 1:
            raise erreur("Dressmond ne peut pas porter plusieurs attaques lors d'un même tour")

        avantage = surprise + (classe is not None) * (classe == cible.classe - 1) + cible.lien

        dommages_tot = 0
        # Attaques multiples
        for _ in range(nombre):
            dommages = 0
            # Cas si Crowe a une arme de sang (attaquant)
            if isinstance(self, derniere_main) and self.arme_valeur is not None:
                if avantage == 0:
                    dommages = max(np.random.binomial(self.valeur_attaque, p), self.arme_valeur)
                elif avantage > 0:
                    dommages = max(np.random.binomial(self.valeur_attaque, p), np.random.binomial(self.valeur_attaque, p),
                                   self.arme_valeur)
                elif avantage < 0:
                    dommages = min(max(np.random.binomial(self.valeur_attaque, p), self.arme_valeur),
                                   max(np.random.binomial(self.valeur_attaque, p), self.arme_valeur))

            # Cas si Vania attaque avec surprise
            elif isinstance(self, mezsaros) and surprise:
                if avantage == 0:
                    dommages = np.random.binomial(self.valeur_attaque*self.valeur_attaque, p)
                elif avantage > 0:
                    dommages = max(np.random.binomial(self.valeur_attaque*self.valeur_attaque, p), np.random.binomial(self.valeur_attaque*self.valeur_attaque, p))
                elif avantage < 0:
                    dommages = min(np.random.binomial(self.valeur_attaque*self.valeur_attaque, p), np.random.binomial(self.valeur_attaque*self.valeur_attaque, p))


            # Cas usuel
            else:
                if avantage == 0:
                    dommages = np.random.binomial(self.valeur_attaque, p)
                elif avantage > 0:
                    dommages = max(np.random.binomial(self.valeur_attaque, p), np.random.binomial(self.valeur_attaque, p))
                elif avantage < 0:
                    dommages = min(np.random.binomial(self.valeur_attaque, p), np.random.binomial(self.valeur_attaque, p))

            dommages_tot += dommages

        # On applique les dégâts
        self.degats(cible, dommages_tot)


    # Appliquer des dommages à un autre joueur
    def degats(self, cible, dommages):

        # Si on tue sa cible
        if dommages >= cible.ps:
            print(cible.nom + " subit " + str(cible.ps) + " dommages")
            cible.ps = 0
            print(cible.nom + " meurt")
            cible.defuite()
            if cible.nom == "Loup":
                deloup()

        # Sinon, on regarde les dommages infligés
        else:
            cible.ps -= dommages
            print(self.nom + " inflige " + str(dommages) + " dommages à " + cible.nom)
            print(cible.nom + " est désormais à " + str(cible.ps) + " PS")
            cible.etat()


    # Dépenser des PA ou des PS
    def depense(self, pa = 0, ps = 0):

        if not isinstance(pa, int) or not isinstance(ps, int):
            raise erreur("Coût non entier")

        if ps < 0 or pa < 0:
            raise erreur("Coût négatif")

        if ps > self.ps:
            raise erreur(self.nom + " n'a plus assez de PS")

        else:
            self.ps -= ps

            if self.ps < 0.25 * self.ps0:
                print(self.nom + " est mal en point")

        if pa > 0 and self.pa == 0:
            raise erreur(self.nom + " n'a plus de PA")
        else:
            if pa > self.pa:
                self.pa = 0
                print(self.nom + " n'a maintenant plus de PA")
            else:
                self.pa -= pa


    # Connaître si un joueur est un bonne forme ou est en dessous de 25% de ses PS
    def etat(self):
        if self.ps == 0:
            print(self.nom + " est décédé")
        elif self.ps > 0.25 * self.ps0:
            print(self.nom + " est encore en bonne forme")
        else:
            print(self.nom + " est mal en point")
            if self.infecte and self.nom != "Vania":
                print(self.nom + " souffre des effets du virus")


    # Permet de savoir si un joueur peut agir à son tour
    # Cela permet de prendre en compte le fait qu'un perso peut se faire immobiliser
    # avant son tour de jeu dans un même round
    def agir(self):
        if self.ps <= 0:
            raise erreur(self.nom + " est mort")
        else:
            # Si n'est pas stun, peut à priori agir
            if self.stun <= 0 and self.etourdi == 0:
                self.stun_raison = None
                self.etourdi_tour = False

                # Sauf s'il a des liens de sang.
                # S'il était stun, il n'aurait pas pu tenter de s'en libérer
                if not self.lien:
                    print(self.nom + " peut agir")
                else:
                    print(self.nom + " est restreint par des liens de sang et ne peut pas se déplacer")
                    print(self.nom + " peut toutefois les briser avec une attaque")
                    print("MJ : Utiliser la commande delien")

            # Si stun ou étourdi, doit tenter de sortir de sa condition
            else:
                # Si stun
                if self.stun > 0:
                    self.stun -= 1
                    print(self.nom + " est immobilisé(e) et ne peut agir")
                    print("Cause : " + self.stun_raison)

                    # Si étourdi
                if self.etourdi > 0:
                    # S'il vient de se faire étourdir
                    if self.etourdi_tour:
                        print(self.nom + " vient de se faire étourdir")
                        print(self.nom + " ne peut donc pas agir")
                        self.etourdi_tour = False

                    # Sinon, il peut tenter de se libérer
                    else:
                        succes = (random() < self.etourdi)
                        if succes:
                            self.etourdi = 0
                            print(self.nom + " reprend connaissance")
                            print("Il ne peut toutefois pas agir ce tour pour reprendre ses esprits")
                        else:
                            print(self.nom + " est inconscient")


        # Actualiser la fuite
        if self.fuite is not None:
            if self.fuite == 1:
                self.fuite = None
                print(self.nom + " a réussi à fuir")
                if isinstance(self, pnj):
                    self.desengage()
            else:
                self.fuite -= 1
                print(self.nom + " essaye de fuir, ses actions sont limitées à cette fin")


    # Faire le regain de PA, sera utilisé dans une fonction globale
    def regain(self):
        self.pa = pa_max


    # Print les infos et attributs du personnage
    def info(self):
        return (self.__dict__)


    # Sentir l'aura d'un autre vampire pour tenter d'estimer ses caractéristiques
    def sentir(self, cible, pa):
        # pa est le nombre de pa que le joueur dépense
        if pa > 10:
            raise erreur("Le maximum de PA pour cette action est 10")

        self.depense(pa=pa)

        delta = self.rang - cible.rang
        chance = pa * exp(-delta / 3) / 10

        # Tirages aléatoires. S'ils sont plus petits que la chance, l'événement associé se produit
        succes = random()
        reperer = random()

        # Cas particulier de Dressmond
        if cible.nom == "Dressmond":
            if reperer <= chance:
                print(
                    "L'aura de Dressmond était si forte que " + self.nom + " n'a pas réussi à l'analyser et s'est en plus fait(e) repérer par celui-ci")
            else:
                print(
                    "L'aura de Dressmond était si forte que " + self.nom + " n'a pas réussi à l'analyser mais " + self.nom + "ne s'est pas fait(e) repérer")
        else:
            reussite = (succes <= chance)

            # Informations obtenues en cas d'échec
            delta_min = +3 * log(10 / pa)
            gen_min = int(self.rang + delta_min + 1)

            if reperer <= chance:
                if reussite:
                    print(self.nom + " a réussi à analyser l'aura de " + cible.nom + " mais s'est fait(e) repérer")
                    if cible.nom == "Crowe":
                        print("MJ : Donner les informations de Crowe")
                else:
                    print(
                        self.nom + " a seulement réussi à découvrir que " + cible.nom + " était de génération supérieure à " + str(
                            gen_min) + " et s'est en plus fait(e) repérer")
            else:
                if reussite:
                    print(self.nom + " a réussi à analyser l'aura de " + cible.nom + " sans se faire repérer")
                    if cible.nom == "Crowe":
                        print("MJ : Donner les informations de Crowe")
                else:
                    print(
                        self.nom + " a seulement réussi à découvrir que " + cible.nom + " était de génération supérieure à " + str(
                            gen_min))


    # Appliquer un stun à un joueur
    def get_stun(self, temps, cause):
        # On conserve uniquement celle qui dure le plus longtemps
            # On perd malheureusement la trace des autres conditions qui peuvent se superposer
        if temps >= self.stun:
            self.stun = temps
            self.stun_raison = cause
            self.defuite()
            print(self.nom + " est immobilisé(e) pendant " + str(temps) + " tours")
            print("Cause : " + cause)
        else:
            print(
                self.nom + " est déjà immobilisé(e) par " + self.stun_raison + " pendant " + str(self.stun) + " tours")


    # Balles en argent du Soul Dream d'Alec
    def argent(self, cible):
        if Alec.munitions == 0:
            raise erreur("Soul Dream n'a plus de munitions")

        Alec.munitions -= 1
        print("Bang !")

        dommages = cible.vitalite
        self.degats(cible, dommages)

        immobilisation = round(0.1 * exp(2 * cible.generation / 3))

        if not isinstance(cible, demi):
            cible.get_stun(immobilisation, "Une balle en argent empêche temporairement la régénération")
            cible.defuite()


    # Lampe à UV d'Alec : Immobilisation et dégâts éventuels
    def lampe(self, cible):

        if Alec.batterie <= 0:
            raise erreur("La lampe n'a plus de batterie")

        # Cas où la lampe est déjà allumée
        if Alec.switch:
            # Si plus assez de batterie
            if Alec.batterie < 6:
                Alec.batterie = 0
                print("La lampe n'a plus de batterie et s'éteint")
                Alec.switch = False

            # Si encore assez de batterie
            else:
                Alec.batterie = max(0, Alec.batterie - 12)

                if cible.nom == "Crowe":
                    print("La lampe ne semble pas avoir d'effet")
                elif cible.nom == "Alec":
                    print("La lampe n'a strictement aucun effet")
                else:

                    dommages = round(0.005 * exp(cible.generation) * cible.vitalite)
                    self.degats(cible, dommages)

                    immobilisation = max(0, (2 / 3) * log(cible.generation) - 1 / 3)

                    succes = random()
                    if succes <= immobilisation:
                        cible.get_stun(1, "Exposition aux ultra-violets, paralysie par douleur")
                        cible.defuite()
                    else:
                        print("La lumière de la lampe semble faire légèrement brûler " + cible.nom)

                if Alec.batterie == 0:
                    print("La lampe finit par s'éteindre")
                    Alec.switch = False

        # Cas où Alec allume la lampe
        else:
            if Alec.batterie < 15:
                Alec.batterie = 0
                print("La lampe ne parvient pas à s'allumer")

            elif Alec.batterie < 21:
                Alec.batterie = 0
                print("La lampe s'allume puis s'éteint aussitôt")

            else:
                Alec.switch = True
                print("La lampe s'allume")
                Alec.batterie = max(0, Alec.batterie - 27)

                if cible.nom == "Crowe":
                    print("La lampe ne semble pas avoir d'effet")
                elif cible.nom == "Alec":
                    print("La lampe n'a strictement aucun effet")
                else:

                    dommages = round(0.005 * exp(cible.generation) * cible.vitalite )
                    self.degats(cible, dommages)

                    immobilisation = max(0, (2 / 3) * log(cible.generation) - 1 / 3)

                    succes = random()
                    if succes <= immobilisation:
                        cible.get_stun(1, "Exposition aux ultra-violets, paralysie par douleur")
                        cible.defuite()
                    else:
                        print("La lumière de la lampe semble faire légèrement brûler " + cible.nom)

                if Alec.batterie == 0:
                    print("La lampe finit par s'éteindre")
                    Alec.switch = False


    # Se libérer des liens de sang de Crowe
    def delien(self):
        liberer = input(self.nom + " se libère-t-il des liens qui l'entravent ?\n")
        if liberer:
            self.lien = False
            print(self.nom + " utilise une attaque pour se libérer")
        else:
            print(self.nom + " est immobilisé")


    # Matraque de Min
    def matraque(self, cible, combat):
        # combat = True ou False
        # Le combat représente si il y a situation de surprise ou non
        if cible.nom == "Vania":
            chance = 0.4
        elif cible.nom == "Alec":
            chance = 0.9
        elif cible.nom == "Crowe":
            chance = 0.5
        elif cible.nom == "Aleister":
            chance = 0.75
        elif cible.nom == "Min":
            chance = 2 / 3
        elif cible.nom == "Dressmond":
            chance = 0.4
        elif cible.nom == "Serviteurs":
            chance = 0.8
        else:
            chance = 0.5

        if not combat:
            succes = (random() < chance)
            if succes:
                cible.defuite()
                print(cible.nom + " est assommé(e) pour " + str(int(12 * (1 + ( chance / (1 - chance)) ** 2))) + " secondes")
            else:
                print(self.nom + " n'est pas arrivée à assommer " + cible.nom)
                print("MJ : Prévenir " + cible.nom)

        if combat:
            succes = (random() < chance / 2)
            if succes:
                print(cible.nom + " est assommé(e)")
                cible.etourdi = min(max(cible.etourdi, chance / 2), 0.95)
                cible.etourdi_tour = True
                cible.defuite()
            else:
                print(self.nom + " n'est pas arrivée à assommer " + cible.nom)


    # Assommer à mains nues
    def assomme(self, cible, combat):
        # combat = True ou False
        # Le combat représente si il y a situation de surprise ou non
        if cible.nom == "Vania":
            chance = 0.4 * self.valeur_attaque / 10
        elif cible.nom == "Alec":
            chance = 0.9 * self.valeur_attaque / 10
        elif cible.nom == "Crowe":
            chance = 0.5 * self.valeur_attaque / 10
        elif cible.nom == "Aleister":
            chance = 0.75 * self.valeur_attaque / 10
        elif cible.nom == "Min":
            chance = (2 / 3) * self.valeur_attaque / 10
        elif cible.nom == "Dressmond":
            chance = 0.4 * self.valeur_attaque / 10
        elif cible.nom == "Serviteurs":
            chance = 0.8 * self.valeur_attaque / 10
        else:
            chance = 0.5 * self.valeur_attaque / 10

        # Ajustement pour Dressmond qui peut voir son attaque augmenter
        if self.nom == "Dressmond":
            chance = chance * self.valeur_attaque0 / self.valeur_attaque

        if not combat:
            succes = (random() < chance)
            if succes:
                print(cible.nom + " est assommé(e) pour " + str(int(12 * (1 + (chance / (1 - chance)) ** 2))) + " secondes")
                cible.defuite()
            else:
                print(self.nom + " n'est pas arrivée à assommer " + cible.nom)
                print("MJ : Prévenir " + cible.nom)

        if combat:
            succes = (random() < chance / 2)
            if succes:
                print(cible.nom + " est assommé(e)")
                cible.etourdi = min(max(cible.etourdi, chance / 2), 0.95)
                cible.etourdi_tour = True
                cible.defuite()
            else:
                print(self.nom + " n'est pas arrivée à assommer " + cible.nom)


    # Boire une poche de sang. Il faut donner le numéro de la poche qui est bue.
    def boire(self, numero_poche):
        poche = poches[numero_poche]
        del poches[numero_poche]

        # Regain en fonction de la compatibilité des groupes sanguins
        if poche[2] == self.groupe:
            gain = 10
        elif self.nom == "Min":
            gain = 8
        elif self.groupe == "O":
            gain = 4
        elif (self.groupe == "AB") and poche[2] == "O":
            gain = 7
        elif self.groupe == "AB":
            gain = 5
        elif poche[2] == "AB":
            gain = 3
        elif poche[2] == "O":
            gain = 5
        else:
            gain = 1

        # Limite max
        self.ps += min(gain, 1.5 * self.ps0 - self.ps)
        print("Vous regagnez quelques PS")

        # Effets de la drogue ou du virus si la poche est contaminée
        if poche[3] != 0:
            self.virus(poche[3])
        if poche[4] != 0:
            self.take_drogue()

        # Remarques éventuelles sur la poche
        if bool(poche[-1]):
            print("Remarques sur la poche : " + poche[-1])


    # Effets de la drogue
    def take_drogue(self):
        self.defuite()
        # Le cas suivant s'explique par le fait qu'une fonction pour faire
            # prendre la drogue à Dressmond par injection existe. Mais cette
            # fonction take_drogue ne s'applique pas à Dressmond dans cette
            # autre fonction injection. Ainsi, le seul cas restant est celui
            # de la consommation d'une poche de sang.
        if self.nom == "Dressmond":
            Dressmond.injection(poche=True)
        else:
            if self.generation == 1:
                temps_immobi = 2
            elif self.generation == 2:
                temps_immobi = 3
            elif self.generation == 3:
                temps_immobi = 7
            elif self.generation == 7:
                temps_immobi = round(7 * 5 / 2)
            else:
                temps_immobi = round((self.generation + 1) * 5 / 2)

            if 5 * temps_immobi > self.stun:
                self.stun = 5 * temps_immobi
                self.stun_raison = "Hallucinations et vertiges"
                print(self.nom + " est pris(e) d'hallucinations et de vertiges pendant quelques moments")
                print(
                    self.nom + " doit rester immobile à terre ou assis les yeux et oreilles bouché(e)s jusqu'à fin de la condition")

            else:
                print(self.nom + " est pris d'hallucinations et vertiges passagers")

        # La drogue augmente les effets du virus
        if self.infecte:
            self.force_infection = 2


    # Boire le sang d'un autre vampire ou joueur
    def suce(self, cible, pourcentage):
        # Pourcentage est le ratio de sang que l'on souhaite boire entre 0 et 1
        if pourcentage > 1 or pourcentage < 0 :
            print("Le pourcentage doit être entre 0 et 1")
        else:
            if cible.groupe == self.groupe:
                gain = 0.5
            elif self.nom == "Min":
                gain = 0.5
            elif self.groupe == "O":
                gain = 0.2
            elif (self.groupe == "AB") and cible.groupe == "O":
                gain = 0.35
            elif self.groupe == "AB":
                gain = 0.25
            elif cible.groupe == "AB":
                gain = 0.15
            elif cible.groupe == "O":
                gain = 0.25
            else:
                gain = 0.05

            absorbe = pourcentage * cible.ps
            cible.ps = max((1 - pourcentage) * cible.ps, 0)

            recup = min(round(gain * absorbe), 1.5 * self.ps0 - self.ps)

            self.ps += recup
            print(self.nom + " regagne " + str(recup) + " PS")
            print(self.nom + " est maintenant à " + str(self.ps) + "PS")

            cible.etat()

            if cible.infecte:
                self.virus(1)


    # Connaître les effets de l'assimilation du virus
    # Cela sert aussi à mettre à jour l'état
    def virus(self, force = 1):
        # force est 1 si dose normale, 2 si dose élevée d'Alec
        if self.ps == 0:
            print(self.nom + " est mort(e)")
        else:

            if self.infecte:
                print("Actualisation de la progression du virus")
            else:
                self.infecte = True
                self.date_infection = time.time()

            if (force == 1) and (self.force_infection == 2):
                print(self.nom + " est déjà infecte(e) par un virus plus fort")
                force = 2

            self.force_infection = force

            if self.nom == "Vania":
                print("Le virus n'aura aucun effet sur Vania")
            elif isinstance(self, demi) and (force != 2):
                print("Le virus n'aura aucun effet sur " + self.nom)
            elif isinstance(self, pnj) :
                print(self.nom + " devient infecté par le virus avec une force de " + str(force))
                print("MJ : En considérer les effets au cas par cas")
            else:
                if self.nom == "Crowe":
                    duree_propagation = 4
                elif self.nom == "Alec":
                    duree_propagation = 4.5
                elif self.nom == "Aleister":
                    duree_propagation = 5
                elif self.nom == "Min":
                    duree_propagation = 2
                elif self.nom == "Dressmond":
                    duree_propagation = 6

                if force == 2:
                    duree_propagation = duree_propagation / 3

                # Temps restant en secondes, et proportionnel au nombre de ps restants
                temps_restant = duree_propagation * 60 * 60 * self.ps / self.ps0

                self.date_mort = self.date_infection + temps_restant

                heure_mort = time.localtime(self.date_mort).tm_hour
                minute_mort = time.localtime(self.date_mort).tm_min

                print(self.nom + " mourra à " + heure_mort.__str__() + ":" + minute_mort.__str__())

                rate = self.ps0 / duree_propagation
                print(self.nom + " perdra " + str(rate) + " PS par heure")

                # Si un personnage a un "stock" de ps supérieur au "stock" de
                # virus qu'il a développé depuis son infection, il est
                # considéré comme mort même si il lui restait encore des ps,
                # qui auraient dû être décomptés par le virus
                if time.time() >= self.date_mort:
                    self.ps = 0
                    print(self.nom + " décède du virus")
                elif (self.date_mort - time.time()) / rate < 0.25 * self.ps0:
                    print(self.nom + " est mal en point et souffre des effets du virus")


    # Utiliser l'antidote de Min
    def takeantidote(self):
        if not Min.antidote:
            raise erreur("Min n'a plus d'antidote")

        Min.antidote = False
        if self.nom == "Vania":
            print("L'antidote n'a aucun effet sur Vania")
        elif (self.nom == "Alec") and (self.force_infection != 2):
            print("L'antidote n'a aucun effet sur Alec")
        elif self.infecte:
            temps_antidote = time.time()
            delta_temps = (temps_antidote - self.date_infection) / 60

            coef_force = 1 + 8 * (self.force_infection == 2)

            chance = 1 / (1 + coef_force * exp((delta_temps - 10) / 2))

            succes = (random() < chance)

            if succes:
                self.infecte = False
                self.date_infection = None
                self.date_mort = None
                self.force_infection = 0
                print("Après quelques instants, l'antidote semble faire effet")
            else:
                print("Après quelques instants, l'antidote semble n'avoir eu aucun effet")
                print(self.nom + " décédera bientôt du virus")

        else:
            print(self.nom + " n'était pas infecte. L'antidote n'a aucun effet")


    # Utiliser la Lance sur une cible
    def lance(self, cible, manche = True):
        global Lance_pouvoirs
        if Lance_pouvoirs:
            if self.nom == cible.nom:
                Lance_pouvoirs = False
                print("La Lance reconnaît les pêchés de l'humanité grâce au sacrifice de " + self.nom)
                print("La pointe de la Lance se brise")
                if self.maudit:
                    print("La lance grâcie " + self.nom + " de sa malédiction")
                    self.maudit = False

            elif isinstance(cible, demi):
                self.maudit = True
                self.degats(cible, cible.vitalite)
                cible.defuite()

            else:
                self.maudit = True
                print(self.nom + " reçoit une malédiction pour avoir utilisé la Lance de Longinus")
                heure_attaque = time.time()

                self.degats(cible, cible.vitalite)

                duree = int(4 * exp(cible.rang / 2))
                print(cible.nom + " est immobilisé pendant " + str(duree) + " minutes")

                cible.get_stun(5 * duree, "La lance empêche la régénération")
                cible.defuite()

                date_reveil = heure_attaque + duree * 60

                heure_reveil = time.localtime(date_reveil).tm_hour
                minute_reveil = time.localtime(date_reveil).tm_min

                print(cible.nom + " ressuscitera à " + heure_reveil.__str__() + ":" + minute_reveil.__str__())
                if manche:
                    print(self.nom + " retire la Lance du corps de " + cible.nom)
                else:
                    print(
                        "La pointe de la Lance reste bloquée dans le corps de " + cible.nom + " jusqu'à ce que " + cible.nom + " ressuscite")

        else:
            print("La lance a perdu ses pouvoirs")
            self.degats(cible, cible.vitalite)


    # Tenter de fuir face à un poursuivant
    def fuir(self, poursuivant):
        self_score = log(1 + (e - 1) * self.ps / self.ps0) * (
            1 + np.random.binomial(self.initiative, p) / 10)
        poursuivant_score = log(1 + (e - 1) * poursuivant.ps / poursuivant.ps0) * (
            1 + np.random.binomial(poursuivant.initiative, p) / 10)

        if self.stun != 0 or self.etourdi != 0:
            print(self.nom + " n'est pas capable de fuir")
        elif self_score < poursuivant_score:
            print(self.nom + " n'a pas réussi à fuir")
        else:
            tours = round(10 * exp(-(self_score - poursuivant_score) * log(10) / 2))
            print(self.nom + " pourra fuir dans " + str(tours) + " tours")
            if self.fuite is not None:
                self.fuite = min(self.fuite, tours)
            else:
                self.fuite = tours


    # Annuler la fuite
    def defuite(self):
        if self.fuite is not None:
            self.fuite = None
            print(self.nom + " est empêché dans sa fuite")


    # Connaître la vitesse de déplacement
    def vitesse(self):
        vit = round(10 * 2 ** (self.initiative / 10))
        vitms = round(derelat(vit * 1000 / 3600))
        vit = round(vitms * 3600 / 1000)
        sprint = round(derelat(vit * 3 * 1000 / 3600))

        # On adopte une notation scientifique pour les grandes vitesses
        # On n'affiche alors que 3 chiffres significatifs, qu'on doit séparer
        if isinstance(self, dressmond) and self.niveau >= 8:

            vit_ordre = int(log(vit) / log(10))
            vit_cs1 = int(vit / 10 ** (int(log(vit) / log(10))))
            vit_cs2 = int((vit - vit_cs1 * 10 ** vit_ordre) / 10 ** (int(log(vit) / log(10)) - 1))

            vitms_ordre = int(log(vitms) / log(10))
            vitms_cs1 = int(vitms / 10 ** (int(log(vitms) / log(10))))
            vitms_cs2 = int((vitms - vitms_cs1 * 10 ** vitms_ordre) / 10 ** (int(log(vitms) / log(10)) - 1))

            sprint_ordre = int(log(sprint) / log(10))
            sprint_cs1 = int(sprint / 10 ** (int(log(sprint) / log(10))))
            sprint_cs2 = int((sprint - sprint_cs1 * 10 ** sprint_ordre) / 10 ** (int(log(sprint) / log(10)) - 1))

            print(self.nom + " peut courir jusqu'à " + str(vit_cs1) + "," + str(vit_cs2) + ".10^" + str(
                vit_ordre) + " km/h, soit " + str(vitms_cs1) + "," + str(vitms_cs2) + ".10^" + str(
                vitms_ordre) + " m/s")
            print("Sa vitesse de sprint est de " + str(sprint_cs1) + "," + str(sprint_cs2) + ".10^" + str(
                sprint_ordre) + " m/s")

        else:
            print(self.nom + " peut courir jusqu'à " + str(vit) + " km/h, soit " + str(vitms) + " m/s")
            print("Sa vitesse de sprint est de " + str(sprint) + " m/s")



class dressmond(vampire):
    def __init__(self, nom, ps, ps0, pa, groupe, classe, generation, rang, vitalite,
                 valeur_attaque, initiative, infecte, date_infection, date_mort, force_infection,
                 stun, stun_raison, etourdi, etourdi_tour, lien, maudit, date_reveil, fuite,
                 valeur_attaque0, initiative0, niveau, mode, conso, drogue):
        vampire.__init__(self, nom, ps, ps0, pa, groupe, classe, generation, rang, vitalite,
                         valeur_attaque, initiative, infecte, date_infection, date_mort, force_infection,
                         stun, stun_raison, etourdi, etourdi_tour, lien, maudit, date_reveil, fuite)
        self.valeur_attaque0 = valeur_attaque0
        self.initiative0 = initiative0
        self.niveau = niveau
        # Niveau actuel du God End Mode
        self.mode = mode
        # Booléen décrivant si son God End Mode est maintenu ou en dégression
        self.conso = conso
        # Consommation de PS à chaque tour
        self.drogue = drogue
        # Nombre de sédatifs restant à Dressmond


    # Monter de niveau
    def godendmode(self, nouveau_niveau):
        if self.niveau >= nouveau_niveau:
            raise erreur("Dressmond est déjà au niveau " + str(self.niveau))
        if (nouveau_niveau <= 4) and (self.ps + round(
                    0.5 * (exp(3 * self.niveau / 4) * (self.niveau != 0) - exp(3 * nouveau_niveau / 4))) <= 0):
            raise erreur("Dressmond n'a plus assez de PS pour monter en niveau")

        self.mode = True
        conso_supplementaire = - 0.5 * (exp(3 * self.niveau / 4) * (self.niveau != 0) - exp(3 * nouveau_niveau / 4))
        # Valeur positive
        # Permet de faire la différence s'il était à n'importe quel niveau au
        # début du tour d'initiative, et qu'il monte de niveau pendant le
        # sien

        self.ps -= round(conso_supplementaire)
        self.conso = round(self.conso + conso_supplementaire)
        self.niveau = nouveau_niveau
        debit = int(self.niveau ** 2.33)
        print("Dressmond augmente son débit sanguin à " + str(debit) + " L/min")
        print("Dressmond passe au niveau " + str(nouveau_niveau))

        if self.ps <= 0:
            self.ps = 0
            print("Les vaisseaux sanguins de Dressmond explosent")
            print("Dressmond meurt")
        else:
            print("Il consomme pour cela " + str(round(conso_supplementaire)) + " PS")
            print("Sa consommation est maintenant de " + str(self.conso) + " PS par tour")
            print("Dressmond est maintenant à " + str(self.ps) + " PS")

            self.valeur_attaque = int(self.valeur_attaque0 * exp(0.6 * self.niveau))
            self.initiative = int(self.initiative0 * exp(0.5 * self.niveau) / 2.6)
            print("L'attaque de Dressmond passe à " + str(self.valeur_attaque))
            print("L'initiative de Dressmond passe à " + str(self.initiative))

            if self.ps <= 0.25 * self.ps0:
                print("Dressmond est mal en point")

            if self.niveau >= 4:
                print(
                    "Quelques blessures s'ouvrent sur le corps de Dressmond, laissant couler un flot continu de sang plus ou moins important")
                print("Les pertes de sang de Dressmond ne sont plus négligeables")
                if self.niveau >= 8:
                    print("Le sang jaillit même sous haute pression, provoquant des hémorragies internes et externes")
                    print("Dressmond consomme une importante quantité de sang")


    # Stopper le God End Mode et redescendre progressivement de niveau
    def stopmode(self):
        if not self.mode:
            raise erreur("Dressmond ne maintient pas ou plus son God End Mode")
        self.mode = False
        print("Dressmond cesse de maintenir son God End Mode")
        print("Le débit sanguin de Dressmond revient progressivement à la normale")


    # Utiliser une injection de drogue
    def injection(self, poche = False):
        if Dressmond.drogue == 0 and not poche:
            return ("Dressmond n'a plus d'injections")
        if not poche:
            Dressmond.drogue -= 1

        if Dressmond.niveau != 0:
            Dressmond.niveau = 0
            Dressmond.conso = 0
            Dressmond.valeur_attaque = Dressmond.valeur_attaque0
            Dressmond.initiative = Dressmond.initiative0
            Dressmond.mode = False
            print("Le sédatif de Dressmond fait effet pour se calmer et retourne au niveau 0")

        self.defuite()
        print("Dressmond est pris d'hallucinations et de vertiges pendant quelques minutes")
        print("Il doit rester immobile à terre ou assis les yeux et oreilles bouché(e)s jusqu'à fin de la condition")

        Dressmond.get_stun(15,"Hallucinations et vertiges à cause de la drogue")


    # Déterminer la portée de l'AoE de Dressmond et les classes de distance
    def aoe_range(self):
        if self.niveau == 0:
            raise erreur("Dressmond ne peut pas effectuer d'AoE au niveau 0")
        else:
            distance =round(0.23*exp(self.niveau))
            print("Dressmond peut effectuer une AoE avec une portée de " + str(distance) + " mètres")
            print("Ne pas oublier les pnjs dans la liste des cibles (serviteurs, sections, gardes,...)")
            print("")
            print("Proximité de 1 : Entre 0 et " + str(round(distance/3)) + " mètres")
            print("Proximité de 2 : Entre " + str(round(distance/3)) + " et " + str(round(2*distance/3)) + " mètres")
            print("Proximité de 3 : Entre " + str(round(2*distance/3)) + " et " + str(distance) + " mètres")


    # Faire une attaque de zone
    def aoe(self, cibles):
        # cibles est la liste des personnages à proximité sous forme de tuple
            # (personnage, proximité) où la proximité est un nombre entre 1 et
            # 3 qui représente la distance qui sépare la cible de Dressmond,
            # appelé classe de distance (cf fonction aoe_range)
        # On la redéfinit localement afin de pouvoir la modifier

        # Gestion des erreurs
        if not isinstance(cibles, list):
            raise erreur("L'argument doit être une liste")
        for x in cibles :
            if not isinstance(x, tuple):
                raise erreur("La liste doit contenir des tuples sous la forme (perso,proximité)")
        for (perso,proximite) in cibles:
            if not isinstance(proximite, int) or proximite > 3 or proximite < 1:
                raise erreur("La classe de proximité ne peut être que 1, 2 ou 3")

        # On compte le nombre de personnages (les pnj peuvent compter pour plusieurs)
        nombre_cibles = 0

        for (perso, proximite) in cibles:
            if isinstance(perso, pnj):
                nombre_cibles += ceil(perso.ps / perso.ps_indiv)
            else :
                nombre_cibles += 1

        # On évalue les dégâts de Dressmond
        total_degats = np.random.binomial(self.valeur_attaque,p)
        print(total_degats)

        aoe_degats = total_degats / nombre_cibles

        # On applique les dégâts, en tenant compte de la diminution liée à la
            # distance (inversement proportionnelle au carré)
        # Il y a l'également un overkill : Tous les dommages de Dressmond doivent
            # être répartis
        while total_degats > 0:

            # Étape 1 : On applique les dommages à tous les personnages
            for (perso, proximite) in cibles :
                if isinstance(perso, pnj):
                    dommages = ceil((perso.ps/perso.ps_indiv) * aoe_degats * multiplicateur(proximite))
                else:
                    dommages = ceil(aoe_degats * multiplicateur(proximite))
                if total_degats < dommages :
                    dommages = total_degats

                total_degats -= min(perso.ps, dommages)
                Dressmond.degats(perso, dommages)

            # Étape 2 : On retire de la liste des cibles les personnages morts
            decalage = 0
            for i in range(len(cibles)):
                if cibles[i - decalage][0].ps <= 0:
                    cibles.remove(cibles[i - decalage])
                    decalage += 1



class chrysalide(vampire):
    def __init__(self, nom, ps, ps0, pa, groupe, classe, generation, rang, vitalite,
                 valeur_attaque, initiative, infecte, date_infection, date_mort, force_infection,
                 stun, stun_raison, etourdi, etourdi_tour, lien, maudit, date_reveil, fuite,
                 antidote, c4_est, c4_ouest, c4_vlad):
        vampire.__init__(self, nom, ps, ps0, pa, groupe, classe, generation, rang, vitalite,
                         valeur_attaque, initiative, infecte, date_infection, date_mort, force_infection,
                         stun, stun_raison, etourdi, etourdi_tour, lien, maudit, date_reveil, fuite)
        self.antidote = antidote
        self.c4_est = c4_est
        self.c4_ouest = c4_ouest
        self.c4_vlad = c4_vlad
        # Booléens indiquant si les explosifs sont encore armés ou non

    def conversion(self, PA):
        if self.pa == 0:
            print("Min n'a plus de PA")
        else:
            if PA <= self.pa:
                self.pa -= PA
                self.ps += PA
                print("Min a désormais " + str(self.pa) + " PA et " + str(self.ps) + " PS")

            else:
                self.ps += self.pa
                self.pa = 0
                print("Min n'avait pas suffisament de PA, ainsi toute sa jauge a été convertie en PS")
                print("Min a désormais " + str(self.pa) + " PA et " + str(self.ps) + " PS")

    def explosion(self, est = False, ouest = False, vlad = False):
        if est:
            if self.c4_est:
                self.c4_est = False
                chance = random()
                if chance < 0.25:
                    dommages = 0
                elif chance < 0.375:
                    dommages = 1
                elif chance < 0.875:
                    dommages = 2
                else:
                    dommages = 3
                print("L'explosif Est explose en faisant " + str(dommages) + " dégats")
                print("MJ : Entrer manuellement les dégâts")
            else:
                print("L'explosif Est a déjà explosé ou ne répond plus")

        if ouest:
            if self.c4_ouest:
                self.c4_ouest = False
                chance = random()
                if chance < 0.25:
                    dommages = 0
                elif chance < 0.375:
                    dommages = 1
                elif chance < 0.875:
                    dommages = 2
                else:
                    dommages = 3
                print("L'explosif Ouest explose en faisant " + str(dommages) + " dégats")
                print("MJ : Entrer manuellement les dégâts")
            else:
                print("L'explosif Ouest a déjà explosé ou ne répond plus")

        if vlad:
            if self.c4_vlad:
                self.c4_vlad = False
                chance = random()
                if chance < 0.25:
                    dommages = 0
                elif chance < 0.375:
                    dommages = 1
                elif chance < 0.875:
                    dommages = 2
                else:
                    dommages = 3
                print("L'explosif dans la chambre explose en faisant " + str(dommages) + " dégats")
                print("MJ : Entrer manuellement les dégâts")
            else:
                print("L'explosif dans la chambre a déjà explosé ou ne répond plus")


class demi(vampire):
    def __init__(self, nom, ps, ps0, pa, groupe, classe, generation, rang, vitalite,
                 valeur_attaque, initiative, infecte, date_infection, date_mort, force_infection,
                 stun, stun_raison, etourdi, etourdi_tour, lien, maudit, date_reveil, fuite,
                 munitions, batterie, switch, prelevements):
        vampire.__init__(self, nom, ps, ps0, pa, groupe, classe, generation, rang, vitalite,
                         valeur_attaque, initiative, infecte, date_infection, date_mort, force_infection,
                         stun, stun_raison, etourdi, etourdi_tour, lien, maudit, date_reveil, fuite)
        self.munitions = munitions
        # Balles en argent
        self.batterie = batterie
        # Durée de batterie restante pour sa lampe à UV
        self.switch = switch
        # Booléan indiquant si la lampe est allumée ou non
        self.prelevements = prelevements
        # Echantillons d'analyse d'Alec


class derniere_main(vampire):
    def __init__(self, nom, ps, ps0, pa, groupe, classe, generation, rang, vitalite,
                 valeur_attaque, initiative, infecte, date_infection, date_mort, force_infection,
                 stun, stun_raison, etourdi, etourdi_tour, lien, maudit, date_reveil, fuite,
                 arme_valeur):
        vampire.__init__(self, nom, ps, ps0, pa, groupe, classe, generation, rang, vitalite,
                         valeur_attaque, initiative, infecte, date_infection, date_mort, force_infection,
                         stun, stun_raison, etourdi, etourdi_tour, lien, maudit, date_reveil, fuite)
        self.arme_valeur = arme_valeur
        # S'il possède une arme et si oui, son nombre de PS

    # Parasitisme de Pharacibr
    def parasite(self, cible, influence, ps):
        # influence est pensée, idée ou action en str

        if ps > 10:
            raise erreur("Le maximum de PS est de 10 pour ce pouvoir")

        if (influence != "pensee") and (influence != "pensée") and (influence != "idee") and (influence != "idée") and (
                    influence != "action"):
            raise erreur("Erreur d'entrée du type d'influence")

        self.depense(ps = ps)

        chance = (ps / 10) * exp(cible.generation / 3) / 2

        if (influence == "idee") or (influence == "idée"):
            chance = chance / 2
        if (influence == "action"):
            chance = chance / 4

        succes = random()

        if cible.nom == "Aleister":
            print("La capacité semble avoir échouée mais Aleister ne devrait avoir rien remarqué")

        elif cible.nom == "Min":
            # À cause de l'assimilation de Min, la capacité marche toujours, les instructions ne sont pas toujours bien comprises
            if random() < 1 / 3:
                print("La capacité semble avoir réussie")
                print("MJ : Aller communiquer à Min l'instruction de Crowe")
            else:
                print("La capacité semble avoir réussie")
                print(
                    "MJ : Aller communiquer à Min une information contraire ou n'ayant rien à avoir avec l'instruction de Crowe")

        else:
            if succes < chance:
                print("La capacité semble avoir réussie")
                print("MJ : Aller communiquer à " + cible.nom + " l'instruction de Crowe")
            else:
                print("La capacité semble avoir échouée")
                print(
                    "MJ : Aller informer " + cible.nom + " qu'il ou elle a senti quelque chose s'infiltrer dans son corps et tenter de l'influencer")

    # Création d'une arme de sang
    def arme(self, ps):
        if ps > 8:
            raise erreur("Le maximum de PS est de 8, la valeur d'attaque de Crowe, pour ce pouvoir")

        self.depense(ps = ps)
        self.arme_valeur = ps
        print("Crowe fait apparaître une arme de sang")

    # Création de liens de sang
    def liens(self, cible):
        self.depense(ps = cible.initiative)

        cible.lien = True
        print("Des liens de sang restreignent maintenant " + cible.nom)
        cible.defuite()


class mezsaros(vampire):
    def __init__(self, nom, ps, ps0, pa, groupe, classe, generation, rang, vitalite,
                 valeur_attaque, initiative, infecte, date_infection, date_mort, force_infection,
                 stun, stun_raison, etourdi, etourdi_tour, lien, maudit, date_reveil, fuite):
        vampire.__init__(self, nom, ps, ps0, pa, groupe, classe, generation, rang, vitalite,
                         valeur_attaque, initiative, infecte, date_infection, date_mort, force_infection,
                         stun, stun_raison, etourdi, etourdi_tour, lien, maudit, date_reveil, fuite)

    # Fonction pour invoquer des loups
    def familier(self, ps):
        if Loup.existe:
            print("Vania a déjà invoqué un loup")
            print("Elle peut toutefois le révoquer avant d'un réinvoquer un nouveau")
            print("MJ : Utiliser la commande deloup")
        else:
            self.depense(ps = ps)
            Loup.existe = True
            Loup.ps = ps
            Loup.ps0 = ps
            Loup.valeur_attaque = Vania.valeur_attaque
            Loup.initiative = Vania.initiative
            Loup.vitalite = ps


# Classe du loup de Vania
class loup(vampire):
    def __init__(self, nom, ps, ps0, pa, groupe, classe, generation, rang, vitalite,
                 valeur_attaque, initiative, infecte, date_infection, date_mort, force_infection,
                 stun, stun_raison, etourdi, etourdi_tour, lien, maudit, date_reveil, fuite, existe):
        vampire.__init__(self, nom, ps, ps0, pa, groupe, classe, generation, rang, vitalite,
                         valeur_attaque, initiative, infecte, date_infection, date_mort, force_infection,
                         stun, stun_raison, etourdi, etourdi_tour, lien, maudit, date_reveil, fuite)
        self.existe = existe


class simonis(vampire):
    def __init__(self, nom, ps, ps0, pa, groupe, classe, generation, rang, vitalite,
                 valeur_attaque, initiative, infecte, date_infection, date_mort, force_infection,
                 stun, stun_raison, etourdi, etourdi_tour, lien, maudit, date_reveil, fuite,
                 transexistence, target=None):
        vampire.__init__(self, nom, ps, ps0, pa, groupe, classe, generation, rang, vitalite,
                         valeur_attaque, initiative, infecte, date_infection, date_mort, force_infection,
                         stun, stun_raison, etourdi, etourdi_tour, lien, maudit, date_reveil, fuite)
        self.transexistence = transexistence
        self.target = target
        # target est la cible du pouvoir de la justice d'Aleister

    # Porter une attaque à un autre joueur
    def attaque(self, cible, classe = None, surprise = False, nombre = 1, rapiere = True):
        # Le vampire attaquant doit faire une prédiction du type vampire de sa cible
        # La classe est la prédiction de l'attaquant sur la classe de sa cible
        # Il faut entrer le nombre correspond à la classe
        # Un vampire défendant n'a cependant pas cette obligation et il n'y a
            # pas besoin de préciser cet argument qui est est nul par défaut

        # Surprise permet de préciser si le vampire attaquant a un avantage
            # de type surprise, stratégique ou autre ...
        # Cela pourra modifier sa valeur d'avantage ou désavantage.
        # En fonction de son éventuelle prédiction, il peut également avoir un désavantage
        # Avantage peut être +1, -1 ou revenir à 0

        dommages_tot = 0
        # Attaques multiples
        for _ in range(nombre):
            dommages = 0
            avantage = surprise + (classe is not None) * (classe == cible.classe - 1) + cible.lien

            if avantage == 0:
                dommages = np.random.binomial(self.valeur_attaque + 2 * rapiere, p)
            if avantage > 0:
                dommages = max(np.random.binomial(self.valeur_attaque + 2 * rapiere, p),
                               np.random.binomial(self.valeur_attaque + 2 * rapiere, p))
            if avantage < 0:
                dommages = min(np.random.binomial(self.valeur_attaque + 2 * rapiere, p),
                               np.random.binomial(self.valeur_attaque + 2 * rapiere, p))

            dommages_tot += dommages

        # On applique les dégâts
        self.degats(cible, dommages_tot)

    # Regard froid d'Aleister
    def regard(self, cible, ps = False):
        # ps permet de dire si Aleister paye avec des ps

        if cible.generation == 0:
            raise erreur("Aleister ne parvient pas à utiliser cette capacité")

        if cible.generation == 1:
            cout = 5
        elif cible.generation == 2:
            cout = 4
        elif cible.generation <= 4:
            cout = 3
        elif cible.generation <= 6:
            cout = 2
        else:
            cout = 1

        if ps:
            self.depense(ps = cout)
            print("La capacité est efficace")
        else:
            self.depense(pa = cout)
            print("La capacité est efficace")

    # Aleister se lie avec un objet
    def link(self, objet, ps = False):
        # ps permet de dire si Aleister paye avec des ps
        cout = 1 + (1 + len(self.transexistence)) ** 2

        if ps:
            self.depense(ps = cout)
            self.transexistence.append(objet)
            print("Aleister s'est maintenant lié avec l'objet : " + objet)


        else:
            self.depense(pa = cout)
            self.transexistence.append(objet)
            print("Aleister s'est maintenant lié avec l'objet : " + objet)

    # Aleister se délie avec un objet
    def delink(self, objet):
        if objet not in self.transexistence:
            print("Aleister n'est pas lié avec l'objet : " + objet)
        else:
            self.transexistence.remove(objet)
            print("Aleister a rompu le lien avec l'objet : " + objet)

    # Let Justice Be Done, Though The Heavens Fall
    def justice(self, cible):
        if self.target is not None:
            print("Aleister est déjà lié avec " + self.target.nom)
        elif isinstance(cible, demi):
            print("Aleister ne peut pas se lier avec un non-vampire")
        else:
            self.depense(ps=1)
            self.target = cible
            print("Aleister se lie avec " + self.target.nom)
            if self.target.nom == "Dressmond":
                print(
                    "Aleister sent toutefois son coeur se serrer dans sa poitrine et lui donner une sensation extrêmement désagréable doublée d'un très mauvais pressentiment. Utiliser ce pouvoir sur Dressmond est absolument terrifiant et lui glace le sang.")

    # Rompre ce lien
    def dejustice(self):
        if self.target is None:
            print("Aleister n'est lié avec personne")
        else:
            print("Aleister rompt son lien avec " + self.target.nom)
            self.target = None


class pnj(vampire):
    def __init__(self, nom, ps, ps0, pa, groupe, classe, generation, rang, vitalite,
                 valeur_attaque, initiative, infecte, date_infection, date_mort, force_infection,
                 stun, stun_raison, etourdi, etourdi_tour, lien, maudit, date_reveil, fuite,
                 ps_indiv, combat):
        vampire.__init__(self, nom, ps, ps0, pa, groupe, classe, generation, rang, vitalite,
                         valeur_attaque, initiative, infecte, date_infection, date_mort, force_infection,
                         stun, stun_raison, etourdi, etourdi_tour, lien, maudit, date_reveil, fuite)
        self.ps_indiv = ps_indiv
        # Ici, ps est le nombre de ps total de l'armée. ps_indiv code celui d'un individu
        self.combat = combat
        # combat est un booléan indiquant si les pnj sont en combat

    # Porter une attaque à un autre joueur
    def attaque(self, cible, classe = None, surprise = False, nombre = 1):
        # Le vampire attaquant doit faire une prédiction du type vampire de sa cible
        # La classe est la prédiction de l'attaquant sur la classe de sa cible
        # Il faut entrer le nombre correspond à la classe
        # Un vampire défendant n'a cependant pas cette obligation et il n'y a
            # pas besoin de préciser cet argument qui est est nul par défaut

        # Surprise permet de préciser si le vampire attaquant a un avantage
            # de type surprise, stratégique ou autre ...
        # Cela pourra modifier sa valeur d'avantage ou désavantage.
        # En fonction de son éventuelle prédiction, il peut également avoir un désavantage
        # Avantage peut être +1, -1 ou revenir à 0

        avantage = surprise + (classe is not None) * (classe == cible.classe - 1) + cible.lien

        dommages_tot = 0
        # Attaques multiples
        for _ in range(nombre):
            dommages = 0
            if avantage == 0:
                dommages = np.random.binomial(self.valeur_attaque, p)
            if avantage > 0:
                dommages = max(np.random.binomial(self.valeur_attaque, p), np.random.binomial(self.valeur_attaque, p))
            if avantage < 0:
                dommages = min(np.random.binomial(self.valeur_attaque, p), np.random.binomial(self.valeur_attaque, p))

                # Dégats de masse contre des autres pnjs
            if isinstance(cible, pnj):
                dommages *= ceil(self.ps / self.ps_indiv)
            else:
                # Sinon, dégats doublés pour représenter l'encerclement et le fait de se faire attaquer par une "armée"
                if ceil(self.ps / self.ps_indiv) >= 2:
                    dommages *= 2

            dommages_tot += dommages

        # On applique les dégâts
        self.degats(cible, dommages)


    # Faire arriver un pnj en phase de combat
    def engage(self):
        self.combat = True
        print(self.nom + " entre en combat")

    # Faire désengager des pnj du combat
    def desengage(self):
        self.combat = False
        print(self.nom + " se retirent du combat")

    # Séparer un groupe de pnj
    def separate(self, nombre, nom):
        # nombre est le nombre de pnj qu'on souhaite détacher

        new_ps = nombre * self.ps_indiv
        self.depense(ps = new_ps)

        global liste_pnj
        liste_pnj.append(
                pnj(nom = nom, ps = new_ps, ps0 = new_ps, pa = self.pa,
                   groupe = self.groupe, classe = self.classe,
                   generation = self.generation, rang = self.rang,
                   vitalite = self.vitalite, valeur_attaque = self.valeur_attaque,
                   initiative = self.initiative, infecte = self.infecte,
                   date_infection = self.date_infection,
                   date_mort = self.date_mort,
                   force_infection = self.force_infection, stun = self.stun,
                   stun_raison = self.stun_raison,
                   etourdi = self.etourdi, etourdi_tour = self.etourdi_tour,
                   lien = self.lien, maudit = self.maudit,
                   date_reveil = self.date_reveil, fuite = self.fuite,
                   ps_indiv = self.ps_indiv, combat = self.combat)
                )

        globals()[nom] = liste_pnj[-1]

# Faire le regain de PA en utilisant la méthode
def regain():
    liste = [Vania, Crowe, Min, Aleister, Dressmond, Alec]

    for perso in liste:
        perso.regain()


# Déterminer l'ordre d'initiative pour un round de combat
def initiative():
    global liste_pnj

    liste = [Vania, Crowe, Min, Aleister, Dressmond, Alec]

    if Loup.existe:
        liste.append(Loup)

    for pnj in liste_pnj:
        if pnj.combat:
            if pnj.ps > 0:
                liste.append(pnj)
            else:
                pnj.desengage()

    # On décompte l'immobilisation éventuelles des persos
    for perso in liste:
        passe = False
        if perso.ps <= 0:
            print(perso.nom + " est mort")
            passe = True
        else:
            # Immobilisation
            if perso.stun > 0:
                perso.stun = max(int(perso.stun - 1), 0)
                print(perso.nom + " ne peut pas agir ce tour")
                print("Cause : " + perso.stun_raison)
                passe = True

            if perso.stun == 0:
                if perso.stun_raison is not None:
                    perso.stun_raison = None

            # Etourdissement
            if perso.etourdi > 0:
                passe = True
                succes = (random() < perso.etourdi)
                if succes:
                    perso.etourdi = 0
                    perso.stun_raison = False
                    print(perso.nom + " reprend connaissance")
                    print(perso.nom + " ne peut toutefois pas agir ce tour pour reprendre ses esprits")

                else:
                    print(perso.nom + " est inconscient")
        if passe:
            liste.remove(perso)

    # On retire l'arme de Crowe s'il en a une
    if Crowe.arme_valeur is not None:
        arme_dispell()

    # On decrease le niveau de Dressmond si besoin
    if (Dressmond.niveau >= 1) and not Dressmond.mode:
        Dressmond.niveau -= 1
        print("Dressmond redescend au niveau " + str(Dressmond.niveau))

        Dressmond.valeur_attaque = int(Dressmond.valeur_attaque0 * exp(0.6 * Dressmond.niveau))
        Dressmond.initiative = int(Dressmond.initiative0 * exp(0.5 * Dressmond.niveau) / 2.6)

        if Dressmond.niveau == 0:
            Dressmond.conso = 0

    if Dressmond.mode or Dressmond.niveau >= 1:
        Dressmond.conso = int(0.5 * exp(3 * Dressmond.niveau / 4))
        Dressmond.ps -= Dressmond.conso
        print("Dressmond pert " + str(Dressmond.conso) + " PS")

        if Dressmond.ps <= 0:
            Dressmond.ps = 0
            Dressmond.mode = False
            print("Dressmond meurt de ses blessures")
        else:
            print("Dressmond est maintenant à " + str(Dressmond.ps) + "PS")

            if Dressmond.ps <= 0.25 * Dressmond.ps0:
                print("Dressmond est mal en point")


    init = [np.random.binomial(perso.initiative, p) for perso in liste]

    joueurs = [perso.nom for perso in liste]

    ordre = [(perso, init_valeur) for init_valeur, perso in sorted(zip(init, joueurs), reverse=True)]
    print("L'ordre d'initiative est le suivant :")
    print("Syntaxe : Perso (nombre d'attaques)")
    print("")

    for (perso, init_valeur) in ordre:
        if isinstance(perso, dressmond):
            nombre_attaques = 1
        else:
            nombre_attaques = round((3 / 4) * exp(init_valeur / 4))
        print(perso + " (" + str(nombre_attaques) + ")")

    print("")
    print("MJ : Ne pas oublier d'utiliser la commande agir() pour chaque personnage")
    print("Elle permet de prendre en compte les immobilisations et la fuite")


# Eteindre la lampe à UV
def lampe_shutdown():
    if Alec.switch:
        print("La lampe est déjà éteinte")
    else:
        Alec.switch = False
        print("La lampe s'éteint")


# Faire disparaitre l'arme de Crowe
def arme_dispell():
    if Crowe.arme_valeur is not None:
        Crowe.arme_valeur = None
        print("L'arme de Crowe disparait")
    else:
        print("Crowe n'a pas d'arme")


# Révoquer le loup de Vania
def deloup():
    if Loup.existe == False:
        print("Aucun loup n'est convoqué")
    else:
        Loup.existe = False
        Loup.ps = 0
        Loup.ps0 = 0
        Loup.valeur_attaque = 0
        Loup.initiative = 0
        Loup.vitalite = 0
        print("Le loup de Vania disparaît")


# Juger Aleister et sa cible lorsqu'on des deux commet un mensonge
def mensonge():
    if Aleister.target is None:
        raise erreur("Aleister n'est lié avec personne")

    Aleister.defuite()
    Aleister.target.defuite()

    if isinstance(Aleister.target, dressmond):
        print("Le coeur d'Aleister inplose. Ce dernier fait une crise cardiaque et du sang innonde son corps")
        Aleister.ps -= 40
        if Aleister.ps <= 0:
            print("Aleister meurt")
        else:
            print("Aleister se relève quelques minutes plus tard")
            print(
                "Aleister est pris d'une peur intense envers Dressmond et sa puissance monstrueuse, qui est probablement la cause de cette dégénération")
            if Aleister.ps < 0.25 * Aleister.ps0:
                print("Aleister est mal en point")

        if Aleister.target.nom == "Dressmond":
            if Dressmond.niveau != 0:
                Dressmond.niveau = 0
                Dressmond.mode = False
                Dressmond.valeur_attaque = Dressmond.valeur_attaque0
                Dressmond.initiative = Dressmond.initiative0
                Dressmond.conso = 0
                print("Dressmond fait une crise cardiaque, ce qui arrête son corps quelques secondes")
                print("Son coeur redémarre cependant très rapidement")
                print("Toutefois, cela a complètement réinitialisé son God End Mode")
            else:
                Dressmond.ps -= 1
                if Dressmond.ps <= 0:
                    print("Dressmond meurt")
                elif Dressmond.ps < 0.25 * Dressmond.ps0:
                    print("Dressmond est mal en point")

    elif isinstance(Aleister.target, chrysalide) and random() < 0.5:
        print("Rien ne se passe")
    else:

        print("Aleister et " + Aleister.target.nom + " sont pris d'une crise cardiaque")

        Aleister.ps -= Aleister.vitalite
        Aleister.target.ps -= Aleister.target.vitalite

        if Aleister.ps <= 0:
            print("Aleister meurt")
        else:
            print("Aleister subit " + str(Aleister.vitalite) + " dégats et tombe à " + str(Aleister.ps) + " PS")
            if Aleister.ps < 0.25 * Aleister.ps0:
                print("Aleister est mal en point")

        if Aleister.target.ps <= 0:
            print(Aleister.target.nom + " meurt")
        else:
            print(Aleister.target.nom + " subit " + str(Aleister.target.vitalite) + " dégats et tombe à " + str(
                Aleister.target.ps) + " PS")
            if Aleister.target.ps < 0.25 * Aleister.target.ps0:
                print(Aleister.target.nom + " est mal en point")


# Tenter de désamorcer un explosif de Min
def defuse(est = False, ouest = False, vlad = False):
    if est:
        if random() < 0.25:
            print("L'explosif est désamorcé")
            Min.c4_est = False
        else:
            Min.explosion(est = True)

    if ouest:
        if random() < 0.25:
            print("L'explosif est désamorcé")
            Min.c4_ouest = False
        else:
            Min.explosion(ouest = True)

    if vlad:
        if random() < 0.25:
            print("L'explosif est désamorcé")
            Min.c4_vlad = False
        else:
            Min.explosion(vlad = True)


# Connaitre l'état des joueurs infectés par le virus
def virus():
    Liste = [Vania, Alec, Crowe, Aleister, Min, Dressmond]
    for perso in Liste:
        if perso.infecte:
            print(perso.nom + " est infecté(e) par le virus")
            perso.virus()
            print("")


# Connaître le type associé à son code (chiffre)
def classe(nombre):
    L = [1, 2, 4, 0, 0.5]
    if nombre not in L:
        print("Ce nombre ne correspond à aucun type")
    if nombre == 1:
        print("Vampire de classe 1")
    if nombre == 2:
        print("Vampire de classe 2")
    if nombre == 4:
        print("Vampire élémentaire")
    if nombre == 0:
        print("Vampire originel")
    if nombre == 0.5:
        print("Demi-vampire")


# Fonctions de relativité pour Dressmond
c = 3.0 * (10 ** 8)


def gamma_to_beta(gamma):
    return sqrt(1 - (1 / (gamma ** 2)))


def derelat(v):
    e_k = (v ** 2) / 2
    gamma = max(1, 1 + (e_k / (c ** 2)))
    if gamma <= 1.00001:
        return v
    beta = gamma_to_beta(gamma)
    return min(v, beta*c)


# Transformer la proximité en multiplicateur de dégâts causé par la distance
    # de l'AoE de Dressmond
def multiplicateur(proximite):
    if proximite == 1:
        return(1)
    elif proximite == 2:
        return(0.5)
    elif proximite == 3:
        return(0.1)
    else :
        raise erreur("La classe de proximité ne peut être que 1, 2 ou 3")


# Faire une ellipse temporelle
def timeskip(minutes):
    liste_attente = [Vania, Alec, Crowe, Aleister, Min, Dressmond] + liste_pnj
    if Loup.existe :
        liste_attente = liste_attente + [Loup]

    # Tant que des personnages ont encore des conditions :
    while minutes > 0 and len(liste_attente) > 0 :
        initiative()
        decalage = 0
        for i in range(len(liste_attente)):
            perso = liste_attente[i - decalage]

            # initiative() permet de gérer toutes les conditions sauf la fuite
            if perso.fuite is not None:
                if perso.fuite == 1:
                    perso.fuite = None
                    print(perso.nom + " a réussi à fuir")
                    if isinstance(perso, pnj):
                        perso.desengage()
                else:
                    perso.fuite -= 1
                    print(perso.nom + " essaye de fuir, ses actions sont limitées à cette fin")

            if perso.etourdi == 0 and perso.stun == 0 and perso.fuite == None:
                liste_attente.remove(perso)
                decalage += 1

        minutes -= 0.2

    if len(liste_attente) > 0 :
        print("Personnages encore affectés par une condition :")
        for perso in liste_attente:
            print(perso.nom)


# Faire une sauvegarde des objets
def save():
    try :
        with open("Vania.file", "wb") as f:
            pickle.dump(Vania, f, pickle.HIGHEST_PROTOCOL)
        with open("Alec.file", "wb") as f:
            pickle.dump(Alec, f, pickle.HIGHEST_PROTOCOL)
        with open("Crowe.file", "wb") as f:
            pickle.dump(Crowe, f, pickle.HIGHEST_PROTOCOL)
        with open("Aleister.file", "wb") as f:
            pickle.dump(Aleister, f, pickle.HIGHEST_PROTOCOL)
        with open("Min.file", "wb") as f:
            pickle.dump(Min, f, pickle.HIGHEST_PROTOCOL)
        with open("Dressmond.file", "wb") as f:
            pickle.dump(Dressmond, f, pickle.HIGHEST_PROTOCOL)
        with open("Loup.file", "wb") as f:
            pickle.dump(Loup, f, pickle.HIGHEST_PROTOCOL)
        with open("liste_pnj.file", "wb") as f:
            pickle.dump(liste_pnj, f, pickle.HIGHEST_PROTOCOL)
        with open("poches.file", "wb") as f:
            pickle.dump(poches, f, pickle.HIGHEST_PROTOCOL)
        with open("temps_debut.file", "wb") as f:
            pickle.dump(temps_debut, f, pickle.HIGHEST_PROTOCOL)
        with open("Lance_pouvoirs.file", "wb") as f:
            pickle.dump(Lance_pouvoirs, f, pickle.HIGHEST_PROTOCOL)
        print("Données sauvegardées")
    except :
        print("Aucune données à sauvegarder")


# Charger une sauvegarde des objets
def load():
    demande = input("Voulez-vous charger la dernière sauvegarde des objets ? ")
    if demande == "Oui" :
        confirmation= input("Êtes-vous sûr ? Cela effacera les données actuelles. ")
        if confirmation == "Oui":
            with open("Vania.file", "rb") as f:
                global Vania
                Vania = pickle.load(f)
            with open("Alec.file", "rb") as f:
                global Alec
                Alec = pickle.load(f)
            with open("Crowe.file", "rb") as f:
                global Crowe
                Crowe = pickle.load(f)
            with open("Aleister.file", "rb") as f:
                global Aleister
                Aleister = pickle.load(f)
            with open("Min.file", "rb") as f:
                global Min
                Min = pickle.load(f)
            with open("Dressmond.file", "rb") as f:
                global Dressmond
                Dressmond = pickle.load(f)
            with open("Loup.file", "rb") as f:
                global Loup
                Loup = pickle.load(f)
            with open("liste_pnj.file", "rb") as f:
                global liste_pnj
                liste_pnj = pickle.load(f)
            with open("poches.file", "rb") as f:
                global poches
                poches= pickle.load(f)
            with open("temps_debut.file", "rb") as f:
                global temps_debut
                temps_debut = pickle.load(f)
            with open("Lance_pouvoirs.file", "rb") as f:
                global Lance_pouvoirs
                Lance_pouvoirs = pickle.load(f)

            # Recharger les PNJs supplémentaires qui ont été créés
            for i in range(6, len(liste_pnj)):
                pnj = liste_pnj[i]
                globals()[pnj.nom] = pnj


# Initialiser la murder
def initialisation():
    demande = input("Voulez-vous faire débuter la murder ? S'il existe des données actuelles, elles seront sauvegardées puis réinitialisées ")
    if demande == "Oui":

        save()

        # Supprimer les PNJs supplémentaires qui avaient été créés
        # Ils sont sauvegardés dans la liste, et seront re-créés lors du load()
        global liste_pnj
        try :
            for i in range(6, len(liste_pnj)):
                globals()[liste_pnj[i].nom] = None
        except :
            pass

        global p
        # coefficient p de la loi binomiale
        p = 0.6
        global pa_max
        pa_max = 20

        global Vania
        Vania = mezsaros(nom  =  "Vania", ps = 500, ps0 = 500, pa = pa_max, groupe = "AB", classe = 4,
                         generation = 3, rang = 1, vitalite = 5, valeur_attaque = 5, initiative = 15,
                         infecte = True, date_infection = None, date_mort = None, force_infection = 0, stun = 0,
                         stun_raison = None, etourdi = 0, etourdi_tour = False, lien = False, maudit = False, date_reveil = None, fuite = None)

        global Alec
        Alec = demi(nom = "Alec", ps = 30, ps0 = 30, pa = pa_max, groupe = "B", classe = 0.5,
                    generation = 7, rang = 7, vitalite = 1, valeur_attaque = 4, initiative = 2,
                    infecte = False, date_infection = None, date_mort = None, force_infection = 0,
                    stun = 0, stun_raison = None, etourdi = 0, etourdi_tour = False, lien = False, maudit = False, date_reveil = None, fuite = None,
                    munitions = 9, batterie = 300, switch = False, prelevements = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

        global Crowe
        Crowe = derniere_main(nom = "Crowe", ps = 80, ps0 = 80, pa = pa_max, groupe = "O", classe = 4,
                              generation = 5, rang = 5, vitalite = 3, valeur_attaque = 8, initiative = 10,
                              infecte = False, date_infection = None, date_mort = None, force_infection = 0,
                              stun = 0, stun_raison = None, etourdi = 0, etourdi_tour = False, lien = False, maudit = False, date_reveil = None,
                              fuite = None,
                              arme_valeur = None)

        global Aleister
        Aleister = simonis(nom = "Aleister", ps = 130, ps0 = 130, pa = pa_max, groupe = "AB", classe = 0,
                           generation = 4, rang = 4, vitalite = 4, valeur_attaque = 8, initiative = 7,
                           infecte = False, date_infection = None, date_mort = None, force_infection = 0,
                           stun = 0, stun_raison = None, etourdi = 0, etourdi_tour = False, lien = False, maudit = False, date_reveil = None,
                           fuite = None,
                           transexistence = [], target = None)

        global Min
        Min = chrysalide(nom = "Min", ps = 300, ps0 = 300, pa = pa_max, groupe = "O", classe = 2,
                         generation = 5, rang = 5, vitalite = 6, valeur_attaque = 6, initiative = 6,
                         infecte = False, date_infection = None, date_mort = None, force_infection = 0,
                         stun = 0, stun_raison = None, etourdi = 0, etourdi_tour = False, lien = False, maudit = False, date_reveil = None,
                         fuite = None, antidote = True,
                         c4_est = True, c4_ouest = True, c4_vlad = True)

        global Dressmond
        Dressmond = dressmond(nom = "Dressmond", ps = 1500, ps0 = 1500, pa = pa_max, groupe = "A", classe = 1,
                              generation = 4, rang = 1, vitalite = 10, valeur_attaque = 30,
                              initiative = 4, infecte = False, date_infection = None, date_mort = None, force_infection = 0,
                              stun = 0, stun_raison = None, etourdi = 0, etourdi_tour = False, lien = False, maudit = False, date_reveil = None,
                              fuite = None,
                              valeur_attaque0 = 30, initiative0 = 4, niveau = 0, mode = False, conso = 0, drogue = 2)

        global Loup
        Loup = loup(nom = "Loup", ps = 0, ps0 = 0, pa = 0, groupe = "AB", classe = 4,
                    generation = 4, rang = 4, vitalite = 0, valeur_attaque = 0, initiative = 0,
                    infecte = True, date_infection = None, date_mort = None, force_infection = 0,
                    stun = 0, stun_raison = None, etourdi = 0, etourdi_tour = False, lien = False, maudit = False, date_reveil = None, fuite = None,
                    existe = False)

        global Serviteurs
        Serviteurs = pnj(nom = "Serviteurs", ps = 210, ps0 = 210, pa = pa_max, groupe = "B", classe = 0,
                         generation = 6, rang = 6, vitalite = 3, valeur_attaque = 3, initiative = 3,
                         infecte = False, date_infection = None, date_mort = None, force_infection = 0,
                         stun = 0, stun_raison = None, etourdi = 0, etourdi_tour = False, lien = False, maudit = False, date_reveil = None,
                         fuite = None,
                         ps_indiv = 30, combat = False)

        global Gardes
        Gardes = pnj(nom = "Gardes", ps = 750, ps0 = 750, pa = pa_max, groupe = "AB", classe = 2,
                     generation = 6, rang = 6, vitalite = 5, valeur_attaque = 5, initiative = 5,
                     infecte = False, date_infection = None, date_mort = None, force_infection = 0,
                     stun = 0, stun_raison = None, etourdi = 0, etourdi_tour = False, lien = False, maudit = False, date_reveil = None,
                     fuite = None,
                     ps_indiv = 50, combat = False)

        global Demis
        Demis = pnj(nom = "Demis", ps = 850, ps0 = 550, pa = pa_max, groupe = "A", classe = 0.5,
                    generation = 7, rang = 7, vitalite = 2, valeur_attaque = 3, initiative = 3,
                    infecte = False, date_infection = None, date_mort = None, force_infection = 0,
                    stun = 0, stun_raison = None, etourdi = 0, etourdi_tour = False, lien = False, maudit = False, date_reveil = None, fuite = None,
                    ps_indiv = 17, combat = False)

        global Section1
        Section1 = pnj(nom = "Section 1", ps = 300, ps0 = 300, pa = pa_max, groupe = "AB", classe = 1,
                       generation = 7, rang = 7, vitalite = 3, valeur_attaque = 7, initiative = 9,
                       infecte = False, date_infection = None, date_mort = None, force_infection = 0,
                       stun = 0, stun_raison = None, etourdi = 0, etourdi_tour = False, lien = False, maudit = False, date_reveil = None,
                       fuite = None,
                       ps_indiv = 30, combat = False)

        global Section2
        Section2 = pnj(nom = "Section 2", ps = 300, ps0 = 300, pa = pa_max, groupe = "AB", classe = 1,
                       generation = 7, rang = 7, vitalite = 3, valeur_attaque = 7, initiative = 9,
                       infecte = False, date_infection = None, date_mort = None, force_infection = 0,
                       stun = 0, stun_raison = None, etourdi = 0, etourdi_tour = False, lien = False, maudit = False, date_reveil = None,
                       fuite = None,
                       ps_indiv = 30, combat = False)

        global Section3
        Section3 = pnj(nom = "Section 3", ps = 300, ps0 = 300, pa = pa_max, groupe = "AB", classe = 1,
                       generation = 7, rang = 7, vitalite = 3, valeur_attaque = 7, initiative = 9,
                       infecte = False, date_infection = None, date_mort = None, force_infection = 0,
                       stun = 0, stun_raison = None, etourdi = 0, etourdi_tour = False, lien = False, maudit = False, date_reveil = None,
                       fuite = None,
                       ps_indiv = 30, combat = False)

        liste_pnj = [Serviteurs, Gardes, Demis, Section1, Section2, Section3]

        global poches
        poches = [[1, "Bureau", "B", 0, 1, ""], [1, "Frigo", "B", 0, 0, ""], [2, "Frigo", "B", 0, 0, ""],
                  [3, "Frigo", "B", 0, 0, ""], [4, "Frigo", "B", 0, 0, ""], [1, "Frigo", "O", 0, 0, ""],
                  [2, "Frigo", "O", 0, 0, ""], [1, "Frigo", "AB", 0, 0, ""], [1, "Alec", "O", 1, 0, ""],
                  [2, "Alec", "O", 2, 0, ""], [1, "Vania", "AB", 0, 0, ""], [2, "Vania", "AB", 0, 0, ""],
                  [3, "Vania", "AB", 0, 0, ""], [4, "Vania", "AB", 0, 0, ""], [5, "Vania", "AB", 0, 0, ""]]
        # poches de sang :
            # Numéro dans la localisation et le groupe
            # Localisation
            # Groupe
            # Contaminé par le virus (2 ou 1 ou 0) (2 est la dose super forte d'Alec)
            # Contaminé par la drogue (1 ou 0)
            # Autres notes, commentaires, ...

        global Lance_pouvoirs
        Lance_pouvoirs = True
        # La lance possède ses pouvoirs

        global temps_debut
        temps_debut = time.localtime()
        global t
        t = time.mktime(temps_debut)
        global heure_debut
        heure_debut = temps_debut.tm_hour
        global minute_debut
        minute_debut = temps_debut.tm_min

        print("Début de la murder : " + heure_debut.__str__() + ":" + minute_debut.__str__())

    else:
        print("Échec de l'initialisation")
