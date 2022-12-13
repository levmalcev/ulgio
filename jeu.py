import pygame, random
from Maps import maps
from Cris import cris
from Dialogues import dialogues

# C'est dans la classe "Monde" que se passe la plupart des actions les plus importantes.
class Monde():
	def __init__(self):
		self.entites = []
		self.listeMonstres = [0]
		self.joueur = None
		self.map = maps.MAP_1
		self.niveauFini = False

		# On va dessiner le jeu sur un objet Surface, calqueJeu, que nous
		# déplacerons sur la fenêtre selon le scrolling de la map.

		self.dimCalque = (len(self.map[0])*32, len(self.map)*32)
		self.calqueJeu = pygame.Surface(self.dimCalque)
		self.scroll = 0
		self.scrollStep = 0

		# Map
		self.mapSprite = pygame.image.load("images/map_1.png")
		self.sol_boss = pygame.image.load("images/sol.png")
		self.pilierBoss = pygame.image.load("images/pilier.png")
		self.pilierPosition = 448

		self.spriteBoiteCognee = pygame.transform.scale(pygame.image.load("images/boiteCognee.png"), (32,32))
		self.boitesCognees = []

		# Physique
		self.gravite = 0.002

		self.debug = False
		self.debugFont = pygame.font.Font("police/Verdana.ttf", 10)

		# Gestion de l' "histoire"
		self.etape = 0
		self.chronoEtape = 0
		self.changeMapChrono = 0

	# Réinitialisation du monde lorsqu'on change de niveau, on se débarasse des entités indésirables
	def initMonde(self):
		self.boitesCognees = []
		self.scroll = 0
		self.scrollStep = 0
		self.listeMonstres = [0]
		for entite in self.entites:
			if not entite.type == "joueur" and not entite.type == "porte":
				entite.estMort = True
				entite.position[1] = 1000

	# Passage au niveau 2
	def changeMap(self):
		global NIVEAU

		NIVEAU = 2
		self.initMonde()
		i = 0
		while i < len(self.entites):
			if not self.entites[i].type == "joueur":
				self.entites.pop(i)
				i += 1

		self.joueur.position[0] = 16
		self.joueur.position[1] = 416

		self.map = maps.MAP_2
		self.mapSprite = pygame.image.load("images/map_boss.png")
		self.dimCalque = (len(self.map[0])*32, len(self.map)*32)
		self.calqueJeu = pygame.Surface(self.dimCalque)

		self.niveauFini = False

		self.joueur.controlable = False
		self.etape = 1

	# Fonction permettant de faire avancer le scénario en faisant des pauses entre les scènesself.
	# Lors du passage au niveau 2, il y a un dialogue avec FLAPPY et des animations dans la map (le pilier qui bloque l'entrée)
	def histoire(self):
		global EN_JEU
		tempsMaintenant = pygame.time.get_ticks()
		if not self.etape == 0:
			if self.etape == 1:
				if self.joueur.position[0] < 192:
					self.joueur.marcheEnCours = 1
				else:
					if self.chronoEtape == 0:
						self.joueur.marcheEnCours = 0
						self.chronoEtape = tempsMaintenant + 1000
				if self.chronoEtape and tempsMaintenant > self.chronoEtape:
					self.chronoEtape = 0
					self.etape = 2
					SON_PILIER.play()

			elif self.etape == 2:
				if self.pilierPosition > 352:
					self.gererPilier()
				else:
					self.etape = 3

			elif self.etape == 3:
				self.joueur.controlable = True
				if self.chronoEtape == 0:
					self.chronoEtape = tempsMaintenant + 1000
				if self.chronoEtape and tempsMaintenant > self.chronoEtape:
					self.chronoEtape = 0
					FLAPPY_RIRE.play()
					self.etape = 4

					self.initFlappy()

			elif self.etape == 4:
				if self.flappy().position[1] >= 352:
					self.etape = 5
					self.flappy().vitesse[1] = 0

			elif self.etape == 5:
				dialManager.nouveauDialogue()
				self.etape = 6

			elif self.etape == 6:
				if dialManager.cptPhrase == len(dialManager.listeDialogues[dialManager.cptDialogue]):
					self.etape = 7
					self.chronoEtape = tempsMaintenant + 3000
					pygame.mixer.music.load("sons/boss.ogg")
					pygame.mixer.music.play(-1)

			elif self.etape == 7:
				if self.flappy().nbVies == 0:
					self.joueur.controlable = False
					self.joueur.marcheEnCours = 0
				if self.chronoEtape and tempsMaintenant < self.chronoEtape:
					txt = menu.police.render("UTILISEZ LE BOUTON [MAJ] POUR RAMASSER UN OEUF", True, (255,255,255))
					taille_txt =  [txt.get_width(), txt.get_height()]
					FENETRE.blit(txt, (DIM_FENETRE[0]//2 - taille_txt[0]//2, DIM_FENETRE[1]//10 * 9 + 10))
				else:
					self.chronoEtape = 0

			elif self.etape == 8:
				if self.chronoEtape and tempsMaintenant > self.chronoEtape:
					SON_VICTOIRE.play()
					self.chronoEtape = tempsMaintenant + 3000
					self.etape = 9

			elif self.etape == 9:
				txt = menu.police.render("VOUS AVEZ BATTU FLAPPY !!!", True, (255,0,0))
				taille_txt =  [txt.get_width(), txt.get_height()]
				FENETRE.blit(txt, (DIM_FENETRE[0]//2 - taille_txt[0]//2, DIM_FENETRE[1]//4))
				if self.chronoEtape and tempsMaintenant > self.chronoEtape:
					dialManager.nouveauDialogue()
					self.chronoEtape = 0
					self.etape = 10

			elif self.etape == 10:
				if dialManager.cptPhrase == len(dialManager.listeDialogues[dialManager.cptDialogue]):
					self.etape = 0

					self.joueur.vitesse[0] = 0

					self.joueur.estMort = True
					self.joueur.controlable = False
					REINIT_EN_COURS = tempsMaintenant

	# Fonction qui gère les derniers moments de FLAPPY
	def bossBattu(self):
		pygame.mixer.music.stop()
		SON_BYEFLAPPY.play()
		self.flappy().estMort = True
		self.flappy().estInvincible = True
		self.flappy().delaiInvincible = pygame.time.get_ticks() + 10000
		self.etape = 8
		self.chronoEtape = pygame.time.get_ticks() + 3000

	# Initialisation de FLAPPY
	def initFlappy(self):
		self.entites.append(Entite([DIM_FENETRE[0]//2 + 100,-105], "flappy"))

		self.flappy().vitesse[1] = 0.15
		self.flappy().sens = -1
		self.flappy().VITESSE_MAX = 0.2

	# Récupération de FLAPPY (plus simple ainsi)
	def flappy(self):
		for flappy in self.entites:
			if flappy.type == "flappy":
				return flappy
				break

	# Position du pilier dans la map de combat contre le boss. Le pilier est animé, il y a une translation vers le haut
	def gererPilier(self):
		self.pilierPosition -= 3

	# Fonction qui s'occupe de renvoyer le type de chaque tile selon son numéro d'identification
	def typeTile(self, x, y):
		if self.map[y][x] == 0:
			return "vide"
		elif self.map[y][x] == 1:
			return "mur"
		elif self.map[y][x] == 2:
			return "piece"
		elif self.map[y][x] == 3:
			return "champi"
		elif self.map[y][x] == 4:
			return "monstre"
		elif self.map[y][x] == 5:
			return "plateforme"
		elif self.map[y][x] == 6:
			return "pilier"

	def dessineMap(self):
		for map_y, ligne in enumerate(self.map):
				for map_x, c in enumerate(ligne):
					hauteur = map_y * maps.T
					largeur = map_x * maps.T
					if self.typeTile(map_x, map_y) == "mur":
						pygame.draw.rect(self.calqueJeu, (0, 0, 0), pygame.Rect(
																  largeur,
																  hauteur,
																  maps.T,
																  maps.T))
					elif self.typeTile(map_x, map_y) == "piece":
						pygame.draw.rect(self.calqueJeu, (0, 255, 0), pygame.Rect(
																	  largeur,
																	  hauteur,
																	  maps.T,
																	  maps.T))

	# Affiche le jeu sur différents "calques" (surfaces)
	def afficheMonde(self):

		self.calqueJeu.blit(self.mapSprite, [0, 0])
		if NIVEAU == 2:
			if self.etape > 1:
				self.calqueJeu.blit(self.pilierBoss, [0, self.pilierPosition])

			self.calqueJeu.blit(self.sol_boss, [0, 448])

		for entite in self.entites:
			if entite.visible:
				if entite.type == "monstre":
					self.calqueJeu.blit(entite.spriteActuel, [int(entite.position[0]) - 32 , int(entite.position[1]) - 16])
					entite.gestionCri()
				elif entite.type == "porte":
					self.calqueJeu.blit(entite.spriteActuel, [int(entite.position[0]) - 32, int(entite.position[1]) - entite.spriteActuel.get_height()+32])
				elif entite.type == "flappy":
					self.calqueJeu.blit(entite.spriteActuel, [int(entite.position[0]) - 34, int(entite.position[1]) - entite.spriteActuel.get_height()])
				elif entite.type == "oeuf":
					if not entite.estTenu:
						self.calqueJeu.blit(entite.spriteActuel, [int(entite.position[0]), int(entite.position[1])])
					else:
						self.calqueJeu.blit(entite.spriteActuel, [int(entite.position[0]), int(entite.position[1]) - 10])
				else:
					self.calqueJeu.blit(entite.spriteActuel, [int(entite.position[0]) - 16, int(entite.position[1])])

		for boite in self.boitesCognees:
			self.calqueJeu.blit(self.spriteBoiteCognee, boite)


		# Fonction de debugging très pratique.
		# Il faut initialiser self.debug à True pour l'essayer.

		if self.debug:
			self.dessineMap()

			# Grille Tiles Map ----------

			i = 1
			while i < self.dimCalque[0]:
				if not i % 32:
					pygame.draw.rect(self.calqueJeu, (0, 0, 0), pygame.Rect(i,
																  0,
																  1,
																  DIM_FENETRE[1]))
					case = self.debugFont.render(str(round(i/32)-1), True, (0,0,0))
					self.calqueJeu.blit(case, [i- 28, 0])
				i += 1
			i = 1
			while i < self.dimCalque[1]:
				if not i % 32:
					pygame.draw.rect(self.calqueJeu, (0, 0, 0), pygame.Rect(0,
																  i,
																  self.dimCalque[0],
																  1))
				i += 1


			# Tracker du player ----------

			# Règles de position
			pygame.draw.rect(self.calqueJeu, (0, 255, 0), pygame.Rect(0,
																  int(self.joueur.position[1]),
																  self.dimCalque[0],
																  1))
			pygame.draw.rect(self.calqueJeu, (0, 0, 255), pygame.Rect(int(self.joueur.position[0]),
																  0,
																  1,
																  DIM_FENETRE[1]))

			# Hitbox du player
			pygame.draw.rect(self.calqueJeu, (255, 0, 0), pygame.Rect(
															  int(self.joueur.position[0]) - 16,
															  int(self.joueur.position[1]),
															  self.joueur.taille,
															  1))
			pygame.draw.rect(self.calqueJeu, (255, 0, 0), pygame.Rect(
															  int(self.joueur.position[0]) - 16,
															  int(self.joueur.position[1])+32,
															  self.joueur.taille,
															  1))
			pygame.draw.rect(self.calqueJeu, (255, 0, 0), pygame.Rect(
															  int(self.joueur.position[0]) - 16,
															  int(self.joueur.position[1]),
															  1,
															  self.joueur.taille))
			pygame.draw.rect(self.calqueJeu, (255, 0, 0), pygame.Rect(
															  int(self.joueur.position[0]) + 16,
															  int(self.joueur.position[1]),
															  1,
															  self.joueur.taille))

			positionX = self.debugFont.render("X : "+str(round(self.joueur.position[0])), True, (0,0,255))
			self.calqueJeu.blit(positionX, [self.joueur.position[0]+5, 10])
			positionY = self.debugFont.render("Y : "+str(round(self.joueur.position[1])), True, (0,255,0))
			self.calqueJeu.blit(positionY, [-self.scroll, self.joueur.position[1]-positionX.get_height()-5])


		FENETRE.blit(self.calqueJeu, [self.scroll,0])

	# Moteur physique de toutes les interractions avec la map.
	def moteurPhysique(self, precedant, maintenant):
		for entite in self.entites:
			temps = maintenant - precedant

			# [[80,160], [720,160], [720,320], [80,320], [80,445], [720,445], [720,160]]
			# C'est la "chorégraphie" de Flappy. Ses allés-retours dans la map sont organisés ici
			if entite.type == "flappy" and self.etape >= 7 and not entite.estInvincible and not entite.estMort:
				posX, posY = entite.position

				if entite.trajetEnCours == [80,160]:
					entite.sens = -1
					if posX > entite.trajetEnCours[0]:
						entite.vitesse[0] = entite.sens * entite.VITESSE_MAX
					else:
						entite.vitesse[0] = 0

					if posY > entite.trajetEnCours[1]:
						entite.vitesse[1] = -entite.VITESSE_MAX
					else:
						entite.vitesse[1] = 0

					if posX <= entite.trajetEnCours[0] and posY <= entite.trajetEnCours[1]:
						entite.sens = 1
						entite.trajetEnCours = [720,160]

				elif entite.trajetEnCours == [720,160] and entite.sens == 1:
					entite.sens = 1
					if posX < entite.trajetEnCours[0]:
						entite.vitesse[0] = entite.sens * entite.VITESSE_MAX
					else:
						entite.vitesse[0] = 0
					entite.vitesse[1] = 0

					if posX >= entite.trajetEnCours[0]:
						entite.trajetEnCours = [720,320]

				elif entite.trajetEnCours == [720,320]:
					entite.sens = -1
					if posY < entite.trajetEnCours[1]:
						entite.vitesse[1] = entite.VITESSE_MAX
					else:
						entite.vitesse[1] = 0
					entite.vitesse[0] = 0

					if posY >= entite.trajetEnCours[1]:
						entite.trajetEnCours = [80,320]

				elif entite.trajetEnCours == [80,320]:
					entite.sens = -1
					if posX > entite.trajetEnCours[0]:
						entite.vitesse[0] = entite.sens * entite.VITESSE_MAX
					else:
						entite.vitesse[0] = 0
					entite.vitesse[1] = 0

					if posX <= entite.trajetEnCours[0]:
						entite.trajetEnCours = [80,445]

				elif entite.trajetEnCours == [80,445]:
					entite.sens = -1
					if posY < entite.trajetEnCours[1]:
						entite.vitesse[1] = entite.VITESSE_MAX
					else:
						entite.vitesse[1] = 0
					entite.vitesse[0] = 0

					if posY >= entite.trajetEnCours[1]:
						entite.trajetEnCours = [720,445]

				elif entite.trajetEnCours == [720,445]:
					entite.sens = 1
					if posX < entite.trajetEnCours[0]:
						entite.vitesse[0] = entite.sens * entite.VITESSE_MAX
					else:
						entite.vitesse[0] = 0
					entite.vitesse[1] = 0

					if posX >= entite.trajetEnCours[0]:
						entite.sens = -1
						entite.trajetEnCours = [720,160]

				elif entite.trajetEnCours == [720,160] and entite.sens == -1:
					entite.sens = -1
					if posY > entite.trajetEnCours[1]:
						entite.vitesse[1] = -entite.VITESSE_MAX
					else:
						entite.vitesse[1] = 0
					entite.vitesse[0] = 0

					if posY <= entite.trajetEnCours[1]:
						entite.trajetEnCours = [80,160]

			elif entite.type == "flappy":
				if entite.estInvincible and not entite.estMort:
					entite.vitesse = [0,0]

				if entite.estMort:
					if maintenant < entite.dernierSouffle:
						entite.vitesse = [0,0]
					else:
						entite.vitesse = [0,0.2]


			# ---------- Mouvement Horizontal

			if entite.type == "joueur" or entite.type == "oeuf":
				# Décélération uniquement si c'est un joueur ou un oeuf
				if not ((entite.accelerationX > 0 and entite.vitesse[0] >= entite.VITESSE_MAX) or \
						(entite.accelerationX) < 0 and entite.vitesse[0] <= -entite.VITESSE_MAX) and \
				   not entite.marcheEnCours == 0:
					entite.vitesse[0] = entite.vitesse[0] + (entite.accelerationX * temps)

				if entite.marcheEnCours == 0:
					if not self.debug:
						if entite.type == "oeuf":
							if entite.vitesse[1] == 0:
								entite.vitesse[0] *= entite.DECELERATION
						else:
							entite.vitesse[0] *= entite.DECELERATION
						if abs(entite.vitesse[0]) < 0.002:
							entite.vitesse[0] = 0
					else:
						entite.vitesse[0] = 0

				if abs(entite.vitesse[0]) > entite.VITESSE_MAX:
					entite.vitesse[0] = entite.VITESSE_MAX * entite.marcheEnCours

				if entite.estBlesse or entite.estMort:
					entite.vitesse[0] = 0

			if self.niveauFini and entite.type == "joueur":
				entite.vitesse[0] = entite.VITESSE_MAX
				entite.marcheEnCours = 1

			nouv_posX = entite.position[0] + entite.vitesse[0] * temps

			# ---------- Mouvement Vertical

			if not entite.type == "flappy":
				Vy = entite.vitesse[1] + (self.gravite * temps)
			else:
				Vy = entite.vitesse[1]

			if Vy > 0.94:
				Vy = 0.94
			nouv_posY = entite.position[1] + Vy * temps

			if not (entite.estMort and entite.type == "monstre") and not entite.type == "flappy":

				# ---------- Collisions avec les blocs SOLIDES

				for map_y, ligne in enumerate(self.map):
					for map_x, c in enumerate(ligne):
						if not self.typeTile(map_x, map_y) == "vide" and not self.typeTile(map_x, map_y) == "monstre":
							if self.typeTile(map_x, map_y) == "pilier" and entite.marcheEnCours == 1:
								# Le pilier à gauche de la map #2 (qui apparait depuis le sol)
								# Est en fait existant dans le tableau de la map, et il est
								# possible de le traverser si on se déplace vers la droite.
								# J'ai fait ça pour que le bonhomme puisse rentrer dans la map lors de l'animation
								# d'entrée dans le niveau de combat
								break

							# hauteur = coté haut du bloc qu'on analyse dans le tour de boucle
							# largeur = côté gauche du bloc qu'on analyse dans le tour de boucle
							# T = 32 (=nb pixels/bloc)
							hauteur = map_y * maps.T
							largeur = map_x * maps.T
							T = maps.T

							droite_entite = entite.position[0] + T//2
							gauche_entite = entite.position[0] - T//2
							haut_entite = entite.position[1]
							bas_entite = entite.position[1] + T

							nouv_droite_entite = nouv_posX + T//2
							nouv_gauche_entite = nouv_posX - T//2
							nouv_haut_entite = nouv_posY
							nouv_bas_entite = nouv_posY + T

							if droite_entite <= largeur: # Si entite vient de la gauche
								# Collision à gauche du BLOC
								if nouv_droite_entite >= largeur and nouv_droite_entite <= largeur+T:

									if nouv_haut_entite > hauteur -T  and nouv_haut_entite < hauteur+T:
										nouv_posX = largeur-T//2
										if entite.type == "joueur":
											entite.vitesse[0] = 0
										else:
											entite.resetMarche()

							elif gauche_entite >= largeur+T:
								# Collision à droite du BLOC

								if nouv_gauche_entite < largeur+T and nouv_gauche_entite > largeur:

									if nouv_haut_entite > hauteur -T + 5 and nouv_haut_entite < hauteur+T:
										nouv_posX = largeur+T+T//2
										if entite.type == "joueur":
											entite.vitesse[0] = 0
										else:
											entite.resetMarche()

							else: # Sinon, collision Y

								if Vy <= 0: # Plafond
									if nouv_haut_entite < hauteur+T and nouv_haut_entite > hauteur:
										if entite.type == "joueur":
											if self.typeTile(map_x, map_y) == "piece" or self.typeTile(map_x, map_y) == "champi":
												self.cogneBoite(map_x, map_y, self.typeTile(map_x, map_y))

										if not self.typeTile(map_x, map_y) == "plateforme":
											Vy = 0
											nouv_posY = hauteur+T
								else: # Sol
									if nouv_bas_entite > hauteur and nouv_bas_entite < hauteur+T:
										Vy = 0
										entite.collisionSol()
										nouv_posY = hauteur - T
										if entite.type == "oeuf":
											if entite.dejaTenu and not entite.estTenu:
												entite.explose()

								if haut_entite <= hauteur+T and not self.typeTile(map_x, map_y) == "plateforme":
									while nouv_posY >= hauteur and nouv_posY <= hauteur+T:
										nouv_posY-= 1

			# Vérification spéciale dans la map du BOSS : on doit absolument éviter les bugs liés à des imprécisions de calcul.
			if NIVEAU == 2 and not entite.type == "flappy":
				if nouv_posY <= 0:
					nouv_posY = 0
					Vy = 0
				elif nouv_posY +T > 448:
					nouv_posY = 448 - T

				if nouv_posX + T/2 > 768:
					nouv_posX = 768 - T/2

			# ---------- Mise à jour des attributs

			entite.vitesse[1] = Vy

			entite.position[0] = nouv_posX
			entite.position[1] = nouv_posY

			# Scrolling

			if entite.type == "joueur":
				if nouv_posX >= DIM_FENETRE[0]//2 and nouv_posX <= self.dimCalque[0] - DIM_FENETRE[0]//2 - 3*32:
					if (entite.marcheEnCours == 1 or entite.marcheEnCours == 0) and self.scroll > -nouv_posX + DIM_FENETRE[0]//2:
						self.scroll = -nouv_posX + DIM_FENETRE[0]//2

			# ---------- Blocage gauche/droite de la map

				if entite.position[0] >= self.dimCalque[0] - entite.taille//2:
					entite.position[0] = self.dimCalque[0] - entite.taille//2
					entite.vitesse[0] = 0

				elif entite.position[0] <= abs(self.scroll) + entite.taille//2:
					entite.position[0] = abs(self.scroll) + entite.taille//2
					entite.vitesse[0] = 0

			# Mort du joueur s'il tombe dans un trou. Disparition de l'entité non-joueur.

			if entite.position[1] >= self.dimCalque[1]:
				if entite.type == "joueur" and not entite.estMort:
					entite.mourir()
					entite.vitesse[1] = -1
				else:
					if not entite.type == "joueur" and not entite.type == "flappy":
						self.entites.remove(entite)

	# Moteur de collisions entre les différentes entités physiques (goombas, pièces, flappy, joueur,...)
	def collisionInterEntites(self):
		j = self.joueur
		T = maps.T
		for monstre in self.entites:
			if monstre.type == "monstre" and not monstre.estMort and not j.estBlesse:
				if j.position[0]-T//2 >= monstre.position[0] - T*1.5 and j.position[0]+T//2 <= monstre.position[0] + T*1.5:
					if j.vitesse[1] > 0:
						if j.position[1] + T >= monstre.position[1] and j.position[1] + T < monstre.position[1] + T and not j.estMort:
							j.ecraseMonstre()
							monstre.mourir()
							j.nbKills += 1
					else:
						if j.position[1] >= monstre.position[1] and j.position[1] <= monstre.position[1]+T:
							if not j.estInvincible and not j.estMort:
								j.blesse()

			if monstre.type == "flappy":
				fill = False
				if j.position[0]-T//2 >= monstre.position[0] - 34 and j.position[0]+T//2 <= monstre.position[0] + 34:
						if j.position[1] >= monstre.position[1] - 60 and j.position[1] <= monstre.position[1]:
							if not j.estInvincible and not j.estMort and not monstre.estInvincible and not monstre.estMort:
								j.blesse()

		for item in self.entites:
			if item.type == "piece" or item.type == "champi":
				if j.position[0]-T//2 >= item.position[0] - T*1.5 and j.position[0]+T//2 <= item.position[0] + T*1.5:
					if j.position[1] >= item.position[1] and j.position[1] <= item.position[1]+T:
						self.entites.remove(item)

						if item.type == "piece":
							SON_PIECE_ATTRAPE.play()
							interface.ajoutePiece()
						elif item.type == "champi":
							SON_CHAMPI.play()
							j.ajouteVie()

			elif item.type == "oeuf":
				if item.vitesse[1] > 0:
					if item.position[1] + T >= self.flappy().position[1] - 100 and item.position[1] + T <= self.flappy().position[1] - 55:
						if item.position[0] >= self.flappy().position[0] - 34 and item.position[0] <= self.flappy().position[0] + 34:
							if item.dejaTenu and not self.flappy().estInvincible:
								item.explose()
								self.flappy().blesse()

	# Lorsqu'une boite est cognée, une image de boite vide prend le dessus sur la map à la position
	# de la boite cognée que l'on renseigne en paramètre à la fonction.
	# type = pièce ou champi.
	def cogneBoite(self, x, y, type):
		posX, posY = x * 32, y * 32
		trouve = False

		for pos in self.boitesCognees:
			if [posX, posY] == pos:
				trouve = True
		if not trouve:
			randVitesse = random.randint(1,10)
			SON_PIECE.play()

			if type == "piece":
				self.entites.append(Entite([posX+16, posY-5], "piece"))
				if randVitesse > 5:
					self.entites[-1].vitesse[0] = 0.02
				else:
					self.entites[-1].vitesse[0] = -0.02
			else:
				self.entites.append(Entite([posX+16, posY-5], "champi"))
				if randVitesse > 5:
					self.entites[-1].vitesse[0] = 0.08
				else:
					self.entites[-1].vitesse[0] = -0.08

			self.boitesCognees.append([posX, posY])

			self.entites[-1].vitesse[1] = -0.5

	# Apparition des monstres ;
	# ils apparaissent lorsqu'on s'approche de leur point de "spawn"
	def monstreSpawner(self):
		if not self.joueur.marcheEnCours == 0:
			for map_y, ligne in enumerate(self.map):
				for map_x, c in enumerate(ligne):
					if self.typeTile(map_x, map_y) == "monstre":
						largeur = map_x * maps.T
						if largeur <= self.joueur.position[0] + DIM_FENETRE[0]//2 + maps.T:
							if self.joueur.position[0] < 6300:
								self.ajouteMonstre(map_x, map_y)

	# On supprime les monstres qu'on ne voit plus sur l'écran
	# pour éviter de calculer leurs aspects physiques inutilement
	def poubelleEntites(self):
		for entite in self.entites:
			if not entite.type == "joueur" and not entite.type == "flappy":
				if entite.position[0] <= self.joueur.position[0] - DIM_FENETRE[0]//2 - maps.T:
					self.entites.remove(entite)

	# Ajout du monstre si détection dans la fonction monstreeSpawner
	def ajouteMonstre(self, map_x, map_y):
		trouve = False
		for monstre_pos in self.listeMonstres:
			if monstre_pos == map_x:
				trouve = True
				break
		if not trouve:
			self.listeMonstres.append(map_x)

			self.entites.append(Entite([map_x*32, map_y*32], "monstre"))

			self.entites[-1].vitesse[0] = -0.08
			self.entites[-1].sens = -1

	# Niveau 1 terminé
	def finirNiveau(self):
		pygame.mixer.music.stop()
		pygame.mixer.music.load("sons/clear.ogg")
		pygame.mixer.music.play(1)

		self.niveauFini = True

	# Gestion des petits nuages quand les oeufs explosent
	def gestionPoofs(self):
		for poof in self.entites:
			if poof.type == "poof":
				if poof.action == "poof4":
					self.entites.remove(poof)

class Entite():
	def __init__(self, position, type):

		# Variables qui décrivent l'état d'une entite du jeu
		# L'entité peut être un goomba, une pièce, un champi, le joueur, FLAPPY, un nuage "poof" ou la porte de sortie finale.

		self.position = position
		self.type = type
		self.estMort = False
		self.nbVies = 3
		self.estBlesse = False
		self.estInvincible = False
		self.controlable = True
		self.nbKills = 0

		self.VITESSE_MAX = 0.2
		self.ACCELERATION = 0.005
		self.DECELERATION = 0.8
		self.IMPULSION_SAUT = 0.8

		self.vitesse = [0,0]
		if self.type == "oeuf":
			self.vitesse[1] = -0.5
			self.expire = pygame.time.get_ticks() + 6000
		self.accelerationX = 0

		self.sautEnCours = True
		self.marcheEnCours = 0
		self.sens = 1

		self.listeSprites = self.get_sprite()

		self.visible = True
		if self.type == "monstre":
			self.action = "marche1"
			self.spriteActuel = self.listeSprites["marche1"]

			self.cri = random.choice(cris.LISTE)
			self.policeCri = pygame.font.Font("police/DTM-Mono.otf", 13)
			self.afficheCri = False
		elif self.type == "flappy":
			self.action = "vol1"
			self.spriteActuel = self.listeSprites["vol1"]
			self.cligneOeil = 0
			self.trajet = [[80,160], [720,160], [720,320], [80,320], [80,445], [720,445], [720,160], [80,160]]
			self.trajetEnCours = [80,160]
			self.tempsDernierOeuf = 0
			self.dernierSouffle = 0
		elif self.type == "poof":
			self.action = "poof1"
			self.spriteActuel = self.listeSprites["poof1"]
		else:
			self.action = "fixe1"
			self.spriteActuel = self.listeSprites["fixe1"]
		self.dernierMomentAnim = 0

		self.delaiBlesse = 0
		self.delaiInvincible = 0
		self.delaiClignote = 0

		self.taille = 32

		self.oeufTenu = None
		self.dejaTenu = False
		self.estTenu = False

	# Délai entre chaque image pour chaque type d'animation pour chaque entité
	def get_delaiAnim(self):
		return {
			"fixe":250,
			"marche":50,
			"marche_monstre":100,
			"chute":50,
			"piece":50,
			"porte":100,
			"flappy":40,
			"poof":30
		}

	# Récupération du dictionnaire de sprites associé à chaque entité
	def get_sprite(self):
		if self.type == "joueur":
			liste = {
				"fixe1": pygame.image.load("images/pizzaboy/fixe1.png"),
				"fixe2": pygame.image.load("images/pizzaboy/fixe2.png"),
				"marche1": pygame.image.load("images/pizzaboy/marche1.png"),
				"marche2": pygame.image.load("images/pizzaboy/marche2.png"),
				"marche3": pygame.image.load("images/pizzaboy/marche3.png"),
				"marche4": pygame.image.load("images/pizzaboy/marche4.png"),
				"marche5": pygame.image.load("images/pizzaboy/marche5.png"),
				"marche6": pygame.image.load("images/pizzaboy/marche6.png"),
				"vol": pygame.image.load("images/pizzaboy/vol.png"),
				"chute1": pygame.image.load("images/pizzaboy/chute1.png"),
				"chute2": pygame.image.load("images/pizzaboy/chute2.png"),
				"blesse": pygame.image.load("images/pizzaboy/blesse.png"),
				"mort": pygame.image.load("images/pizzaboy/mort.png")
			}
			for element in liste:
				if not element == "mort" and not "chute" in element:
					liste[element] = pygame.transform.scale(liste[element], (32,32))
		elif self.type == "monstre":
			liste = {
				"marche1": pygame.image.load("images/flappy/flappy_1.png"),
				"marche2": pygame.image.load("images/flappy/flappy_2.png"),
				"marche3": pygame.image.load("images/flappy/flappy_3.png"),
				"marche4":pygame.image.load("images/flappy/flappy_4.png"),
				"mort": pygame.image.load("images/flappy/flappy_mort.png")
			}
		elif self.type == "piece":
			liste = {
				"fixe1": pygame.transform.scale(pygame.image.load("images/piece_1.png"), (32,32)),
				"fixe2": pygame.transform.scale(pygame.image.load("images/piece_2.png"), (32,32)),
				"fixe3": pygame.transform.scale(pygame.image.load("images/piece_3.png"), (32,32)),
				"fixe4": pygame.transform.scale(pygame.image.load("images/piece_4.png"), (32,32))
			}
		elif self.type == "champi":
			liste = {
				"fixe1": pygame.image.load("images/champi.png")
			}
		elif self.type == "porte":
			liste = {
				"fixe1": pygame.image.load("images/porte_1.png"),
				"fixe2": pygame.image.load("images/porte_2.png"),
				"fixe3": pygame.image.load("images/porte_3.png"),
				"fixe4": pygame.image.load("images/porte_4.png")
			}
		elif self.type == "flappy":
			liste = {
				"vol1": pygame.transform.flip(pygame.image.load("images/flappy/boss_1.png"), True, False),
				"vol2": pygame.transform.flip(pygame.image.load("images/flappy/boss_2.png"), True, False),
				"vol3": pygame.transform.flip(pygame.image.load("images/flappy/boss_3.png"), True, False),
				"vol4": pygame.transform.flip(pygame.image.load("images/flappy/boss_4.png"), True, False),
				"blesse1": pygame.transform.flip(pygame.image.load("images/flappy/boss_blesse.png"), True, False)
			}
		elif self.type == "oeuf":
			liste = {
				"fixe1": pygame.image.load("images/oeuf.png")
			}
		elif self.type == "poof":
			liste = {
				"poof1": pygame.transform.scale(pygame.image.load("images/poof_1.png"), (40,40)),
				"poof2": pygame.transform.scale(pygame.image.load("images/poof_2.png"), (40,40)),
				"poof3": pygame.transform.scale(pygame.image.load("images/poof_3.png"), (40,40)),
				"poof4": pygame.transform.scale(pygame.image.load("images/poof_4.png"), (40,40)),
				"poof5": pygame.transform.scale(pygame.image.load("images/poof_5.png"), (40,40)),
			}
		return liste

	# Animation des sprites des personnes en fonction :
	# - Du temps écoulé depuis la dernière image
	# - De l'état de l'entité (estBlesse, estInvincible, estMort, chute, saut, ...)
	def animeSprites(self, tempsMaintenant):
		if self.type == "joueur":
			if not self.estMort and not self.estBlesse:
				if not self.vitesse[1]:
					if self.marcheEnCours == 0:
						if (tempsMaintenant - self.dernierMomentAnim >= self.get_delaiAnim()["fixe"]) or not (self.action == "fixe1" or self.action == "fixe2"):
							self.dernierMomentAnim = tempsMaintenant
							if not (self.action == "fixe1" or self.action == "fixe2"):
								self.action = "fixe1"
							else:
								if self.action == "fixe1":
									self.action = "fixe2"
								elif self.action == "fixe2":
									self.action = "fixe1"

					elif abs(self.marcheEnCours) == 1:
						if tempsMaintenant - self.dernierMomentAnim >= self.get_delaiAnim()["marche"] or not "marche" in self.action:
							self.dernierMomentAnim = tempsMaintenant

							if not "marche" in self.action:
								self.action = "marche1"
							else:
								if self.action[-1] == "6":
									self.action = "marche1"
								else:
									step = int(self.action[-1])+1
									self.action = "marche"+str(step)

				elif self.vitesse[1] < 0:
					if not self.action == "vol":
						self.dernierMomentAnim = tempsMaintenant
						self.action = "vol"
				elif self.vitesse[1] > 0:
					if tempsMaintenant - self.dernierMomentAnim >= self.get_delaiAnim()["chute"] or not "chute" in self.action:
						self.dernierMomentAnim = tempsMaintenant
						if not "chute" in self.action:
							self.action = "chute1"
						else:
							if self.action == "chute1":
								self.action = "chute2"
							else:
								self.action = "chute1"
			elif self.estMort:
				self.action = "mort"
			elif self.estBlesse:
				if tempsMaintenant < self.delaiBlesse:
					if not self.vitesse[1] == 0:
						self.action = "blesse"
					else:
						self.action = "mort"
				else:
					self.estBlesse = False
					self.controlable = True

			self.spriteActuel = self.listeSprites[self.action]

			if self.sens == -1:
				self.spriteActuel = pygame.transform.flip(self.listeSprites[self.action], True, False)

			if self.estInvincible:
				if tempsMaintenant > self.delaiInvincible:
					self.estInvincible = False
					self.visible = True
				else:
					if tempsMaintenant > self.delaiClignote:
						self.visible = not self.visible
						self.delaiClignote = tempsMaintenant + 100

		elif self.type == "monstre":
			if tempsMaintenant - self.dernierMomentAnim >= self.get_delaiAnim()["marche_monstre"] and not self.estMort:
				self.dernierMomentAnim = tempsMaintenant
				if self.action[-1] == "4":
					self.action = "marche1"
				else:
					step = int(self.action[-1])+1
					self.action = "marche"+str(step)
			elif self.estMort:
				self.action = "mort"

			if self.sens == -1:
				self.spriteActuel = pygame.transform.flip(self.listeSprites[self.action], True, False)
			else:
				self.spriteActuel = pygame.transform.flip(self.listeSprites[self.action], False, False)
		elif self.type == "piece":
			if tempsMaintenant - self.dernierMomentAnim >= self.get_delaiAnim()["piece"]:
				self.dernierMomentAnim = tempsMaintenant
				i = int(self.action[-1])
				i += 1
				if i > 4:
					i = 1
				self.action = "fixe"+str(i)
				self.spriteActuel = self.listeSprites[self.action]

		elif self.type == "porte":
			if tempsMaintenant - self.dernierMomentAnim >= self.get_delaiAnim()["porte"]:
				self.dernierMomentAnim = tempsMaintenant
				i = int(self.action[-1])
				i += 1
				if i > 4:
					i = 1
				self.action = "fixe"+str(i)
				self.spriteActuel = self.listeSprites[self.action]

		elif self.type == "flappy":
			if tempsMaintenant - self.dernierMomentAnim >= self.get_delaiAnim()["flappy"]:
				self.dernierMomentAnim = tempsMaintenant
				i = int(self.action[-1])
				i += 1
				if i > 4:
					i = 1

				self.action = "vol"+str(i)

			if self.estInvincible:
				if tempsMaintenant > self.delaiInvincible:
					self.estInvincible = False
					self.visible = True
				else:
					self.action = "blesse1"
					if tempsMaintenant > self.delaiClignote:
						self.visible = not self.visible
						self.delaiClignote = tempsMaintenant + 50

			if self.estMort:
				self.action = "blesse1"

			self.spriteActuel = self.listeSprites[self.action]
			if self.sens == -1:
				self.spriteActuel = pygame.transform.flip(self.listeSprites[self.action], True, False)
			else:
				self.spriteActuel = pygame.transform.flip(self.listeSprites[self.action], False, False)

		elif self.type == "oeuf":
			self.spriteActuel = self.listeSprites[self.action]

		elif self.type == "poof":
			if tempsMaintenant - self.dernierMomentAnim >= self.get_delaiAnim()["poof"]:
				self.dernierMomentAnim = tempsMaintenant
				i = int(self.action[-1])
				i += 1
				if i > 5:
					i = 1
				self.action = "poof"+str(i)
				self.spriteActuel = self.listeSprites[self.action]

	# Les Goombas crient une phrase au hasard lorsqu'ils voient leur bourreau s'approcher
	def gestionCri(self):
		if self.position[1] > monde.joueur.position[1] and abs(self.position[0] - monde.joueur.position[0]) <= 50:
			self.afficheCri = True
		if self.afficheCri:
			surface_cri = self.policeCri.render(self.cri, True, (255,255,255))
			largeur, hauteur = surface_cri.get_size()
			marge = 10
			pygame.draw.rect(monde.calqueJeu, (255,255,255), ([self.position[0] - largeur//2, self.position[1] - hauteur - 20], [ largeur+15, hauteur+15 ]))
			pygame.draw.rect(monde.calqueJeu, (0,0,0), ([self.position[0] - largeur//2 + 2, self.position[1] - hauteur - 18], [ largeur+11, hauteur+11 ]))

			monde.calqueJeu.blit(surface_cri, (self.position[0] - largeur//2 + marge, self.position[1] - hauteur - 20 + marge//2))

	# Initialisation du joueur
	def initJoueur(self):
		self.nbVies = 1
		self.replace()
		self.vitesse = [0,0]
		self.marcheEnCours = 0
		self.estMort = False
		self.controlable = True
		self.estBlesse = False
		self.estInvincible = False
		self.nbKills = 0
		self.oeufTenu = None

	def replace(self):
		self.position = [64,416]

	# Saut du joueur (impulsion vers le haut)
	def saute(self):
		if not self.sautEnCours:
			self.sautEnCours = True
			self.vitesse[1] = -self.IMPULSION_SAUT
			SON_SAUT.play()

	def ajouteVie(self):
		self.nbVies += 1

	def spring(self):
		self.vitesse[1] = -1.2
		self.sautEnCours = True
		SON_SPRING.play()

	def ecraseMonstre(self):
		self.vitesse[1] = -0.5
		self.sautEnCours = True
		SON_ECRASE.play()

	def deplacement(self, sens):
		if not sens == 0:
			self.accelerationX = sens * self.ACCELERATION
			self.sens = sens
		self.marcheEnCours = sens

	def resetMarche(self):
		self.vitesse[0] = -self.vitesse[0]
		self.sens = - self.sens

	def collisionSol(self):
		self.sautEnCours = False

	# Dégats subits. Si le nb de vies chute à 0, le jeu est fini, on recommence une partie.
	def blesse(self):
		if self.nbVies <= 0:
			return
		tempsMaintenant =  pygame.time.get_ticks()
		if not self.type == "flappy":

			self.nbVies -= 1
			self.vitesse[1] = -0.3

			if self.nbVies == 0:
				self.mourir()
			else:
				rand = random.randint(1,3)
				if rand == 1:
					SON_DOULEUR_1.play()
				elif rand == 2:
					SON_DOULEUR_2.play()
				else:
					SON_DOULEUR_3.play()

				self.marcheEnCours = 0

				self.estBlesse = True
				self.estInvincible = True
				self.controlable = False

				self.delaiBlesse = tempsMaintenant + 1000
				self.delaiInvincible = tempsMaintenant + 3000
		else:
			self.nbVies -= 1
			SON_ECRASE.play()
			if not self.nbVies == 0:
				self.estInvincible = True

				self.delaiInvincible = tempsMaintenant + 1500
			else:
				self.dernierSouffle = tempsMaintenant + 1000
				monde.bossBattu()

	# Mort d'une entité ou du joueur
	def mourir(self):
		global REINIT_EN_COURS

		if self.type == "monstre":
			self.vitesse[1] = -0.4
			self.estMort = True
		elif self.type == "joueur":
			self.vitesse[0] = 0

			pygame.mixer.music.stop()
			SON_GAMEOVER.play()

			self.estMort = True
			self.controlable = False
			REINIT_EN_COURS = tempsMaintenant + 3000

	# Gestion de l'apparition des oeufs ; il ne peut y en avoir que 4 maximum en même temps.
	def gestionOeufs(self, tempsMaintenant):
		if self.type == "flappy" and not self.estInvincible and not self.estMort:
			if tempsMaintenant > self.tempsDernierOeuf:
				self.tempsDernierOeuf = tempsMaintenant + 2500
				cptOeufs = 0
				for entite in monde.entites:
					if entite.type == "oeuf":
						if tempsMaintenant >= entite.expire:
							entite.explose()
						else:
							cptOeufs += 1
				if cptOeufs < 4:
					monde.entites.append(Entite([self.position[0], self.position[1]- 60], "oeuf"))
					FLAPPY_PONDRE.play()

	# Les oeufs explosent après leur temps d'expiration écoulé
	def explose(self):
		monde.entites.append(Entite([self.position[0] - 10, self.position[1]], "poof"))
		if monde.joueur.oeufTenu == self:
			monde.joueur.oeufTenu = None
		monde.entites.remove(self)

	# Récupérer un oeuf et le porter
	def prendOeuf(self):
		if self.oeufTenu == None:
			for oeuf in monde.entites:
				if oeuf.type == "oeuf":
					if abs(oeuf.position[0] - self.position[0]) <= 32 and  abs(oeuf.position[1] - self.position[1]) <= 32:
						self.oeufTenu = oeuf
						oeuf.estTenu = True
						oeuf.dejaTenu = True
						break

	# Jeter un oeuf vers le haut
	def jetteOeuf(self):
		oeuf = self.oeufTenu
		self.oeufTenu = None
		oeuf.estTenu = False
		oeuf.DECELERATION = 0.3
		oeuf.vitesse[0] = self.vitesse[0]
		oeuf.vitesse[1] = self.vitesse[1] - 0.5

	# L'oeuf tenu prend la même position x et y que le joueur
	def gestionoeufTenu(self):
		if not self.oeufTenu == None:
			self.oeufTenu.position[0] = self.position[0] - 16
			self.oeufTenu.position[1] = self.position[1]

# Il s'agit de l'interface au-dessus du jeu, qui indique le nombre de coeurs et de pièces.
class Interface():
	def __init__(self):
		self.nbPieces = 0
		self.maxCours = [4,4,5,4]
		self.contouring = [[9,10], [10,10], [11,10], [10,9], [10,11], [9,9], [11,11], [11,9], [9,11]]

		self.police = pygame.font.Font("police/DTM-Mono.otf", 25)
		self.spritePiece = pygame.transform.scale(pygame.image.load("images/piece_1.png"), (28,28))
		self.spriteCoeur = pygame.transform.scale(pygame.image.load("images/coeur.png"), (28,28))

	def ajoutePiece(self):
		self.nbPieces += 1

	def afficheInterface(self):
		j = 0
		while j < len(self.contouring):
			texte = self.police.render("x{}".format(self.nbPieces), True, (0,0,0))
			hauteur =  texte.get_height()
			FENETRE.blit(texte, (30+self.contouring[j][0],self.contouring[j][1]))
			j+=1

		texte = self.police.render("x{}".format(self.nbPieces), True, (249, 224, 77))
		FENETRE.blit(texte, (40,10))
		FENETRE.blit(self.spritePiece, (10,12))

		i = 0
		while i < monde.joueur.nbVies:
			decalage = 3 - monde.joueur.nbVies
			FENETRE.blit(self.spriteCoeur, (10 + i*37 ,45))
			i += 1

# Gestion de la narration et des dialogues.
class DialManager():
	def __init__(self, liste):
		self.dimDialogue = ((DIM_FENETRE[0]-100, DIM_FENETRE[0]//6),
							(DIM_FENETRE[0]-100 - 12, DIM_FENETRE[0]//6 - 11))

		self.posDialogue = ((50, DIM_FENETRE[1] - self.dimDialogue[0][1] -10),
							(50 + 6, DIM_FENETRE[1] - self.dimDialogue[1][1] -15))
		self.margeTexte = 10

		self.dialogueEnCours = False
		self.listeDialogues = liste
		self.phrase = None
		self.phraseComposee = ""
		self.chronologie = []
		for d in self.listeDialogues:
			self.chronologie.append(False)

		self.cptDialogue = -1
		self.cptPhrase = 0
		self.cptMot = 1
		self.dernierTemps = 0
		self.delai = 50

		self.police = pygame.font.Font("police/DTM-Sans.otf", 20)

	def nouveauDialogue(self):
		if self.cptDialogue < len(self.listeDialogues)-1:
			monde.joueur.deplacement(0)
			self.margeTexte += 1
			self.cptDialogue += 1
			self.cptPhrase = 0
			self.dialogueEnCours = True

	def afficheCaseDialogue(self):
		if self.cptPhrase < len(self.listeDialogues[self.cptDialogue]):
			pygame.draw.rect(FENETRE, (255,255,255), ([self.posDialogue[0][0], self.posDialogue[0][1]], self.dimDialogue[0]))
			pygame.draw.rect(FENETRE, (0,0,0), ([self.posDialogue[1][0], self.posDialogue[1][1]], self.dimDialogue[1]))

	def formatDialogue(self, tempsMaintenant):
		# Ce code fait en sorte de s'occuper de :
		# - Faire apparaitre les mots les uns après les autres avec un délai de self.delai millisecondes
		# - Faire en sorte qu'il y ait un retour à la ligne si on atteint une certaine largeur

		mots = [mot.split(' ') for mot in self.listeDialogues[self.cptDialogue][self.cptPhrase].splitlines()]
		phraseActuelle = ""
		i = 0
		while i < self.cptMot:
			phraseActuelle += str(mots[0][i])
			phraseActuelle += " "
			i += 1

		tabMots = [mot.split(' ') for mot in phraseActuelle.splitlines()]

		if tempsMaintenant - self.dernierTemps >= self.delai and self.cptMot < len(mots[0]):
			if not self.cptMot % 1:
				SON_MOT.play()
			self.cptMot += 1
			self.dernierTemps = tempsMaintenant

		espace = self.police.size(" ")[0]

		pos = [self.posDialogue[1][0] + self.margeTexte,self.posDialogue[1][1] + self.margeTexte]
		x, y = pos

		for ligne in tabMots:
			for mot in ligne:
				word_surface = self.police.render(mot, True, (255,255,255))
				mot_largeur, mot_hauteur = word_surface.get_size()
				if x + mot_largeur >= self.posDialogue[1][0] - self.margeTexte + self.dimDialogue[1][0]:
					x = pos[0]  # reset la position x
					y += mot_hauteur  # repart sur nouvelle ligne
				FENETRE.blit(word_surface, (x, y))
				x += mot_largeur + espace
			x = pos[0]  # remet la position x à 0
			y += mot_hauteur  # repart sur nouvelle ligne

	def afficheDialogue(self, tempsMaintenant):
		if self.cptPhrase < len(self.listeDialogues[self.cptDialogue]):
			self.formatDialogue(tempsMaintenant)
		else:
			self.dialogueEnCours = False

	def prochainePhrase(self):
		# On avance à la prochaine phrase dans self.listeDialogues
		SON_CLIC.play()
		self.phraseComposee = ""
		self.cptMot = 0
		self.cptPhrase += 1

		if not self.chronologie[2] and self.chronologie[1] and self.cptPhrase == len(self.listeDialogues[self.cptDialogue]):
			monde.changeMapChrono = pygame.time.get_ticks() + 2000
			self.chronologie[2] = True

	# Dialogues automatiques à certaines position X
	def dialogue_event(self, posX):
		if posX >= 320 and not self.chronologie[0]:
			self.chronologie[0] = True
			self.nouveauDialogue()
		elif posX >= 6400 and not self.chronologie[1]:
			self.chronologie[1] = True
			self.nouveauDialogue()
			monde.finirNiveau()

class GestionEntrees():
	def __init__(self):

		# Gestionnaire des événements clavier

		self.gc = {}

		self.repeteTouche(self.gc, pygame.K_LEFT, 100, 25)
		self.repeteTouche(self.gc, pygame.K_RIGHT, 100, 25)
		self.repeteTouche(self.gc, pygame.K_UP, 100, 25)
		self.repeteTouche(self.gc, pygame.K_q, 100, 25)
		self.repeteTouche(self.gc, pygame.K_d, 100, 25)
		self.repeteTouche(self.gc, pygame.K_z, 100, 25)

	def traite_entrees(self):
		global EN_JEU
		now = pygame.time.get_ticks()
		self.scan(self.gc)
		events = pygame.event.get()

		for evt in events:
			if evt.type == pygame.QUIT:
				EN_JEU = False

			if not MENU_EN_COURS:
				if monde.joueur.controlable:
					if evt.type == pygame.KEYDOWN:
						if not dialManager.dialogueEnCours:
							if evt.key == pygame.K_RIGHT or evt.key == pygame.K_d:
								monde.joueur.deplacement(1)
							if evt.key == pygame.K_LEFT or evt.key ==  pygame.K_q:
								monde.joueur.deplacement(-1)
							if evt.key == pygame.K_UP or evt.key == pygame.K_z:
								monde.joueur.saute()
							if evt.key == pygame.K_RSHIFT or evt.key == pygame.K_LSHIFT:
								if not monde.joueur.oeufTenu:
									monde.joueur.prendOeuf()
								else:
									monde.joueur.jetteOeuf()
						else:
							if evt.key == pygame.K_RETURN:
									if dialManager.dialogueEnCours:
										dialManager.prochainePhrase()

					if not dialManager.dialogueEnCours:
						if evt.type == pygame.KEYPRESSED:
							if evt.key == pygame.K_RIGHT or evt.key == pygame.K_d:
								monde.joueur.deplacement(1)
							if evt.key == pygame.K_LEFT or evt.key == pygame.K_q:
								monde.joueur.deplacement(-1)

						elif evt.type == pygame.KEYUP:
							if evt.key == pygame.K_RIGHT or evt.key == pygame.K_d:
								if monde.joueur.marcheEnCours == 1:
									monde.joueur.deplacement(0)
							if evt.key == pygame.K_LEFT or evt.key == pygame.K_q:
								if monde.joueur.marcheEnCours == -1:
									monde.joueur.deplacement(0)

			else:
				if evt.type == pygame.KEYDOWN:
					if evt.key == pygame.K_RETURN:
						menu.entrer()

	def _nouveauEtatTouche(self):
		return {
			'actif': False,
			'delai': 0,
			'periode': 0,
			'suivant': 0
		}

	def repeteTouche(self, gc, touche, delai, periode):
		pygame.key.set_repeat()

		if touche in gc:
			entree = gc[touche]
		else:
			entree = self._nouveauEtatTouche()

		entree['delai'] = delai
		entree['periode'] = periode
		self.gc[touche] = entree


	def scan(self, gc):
		maintenant = pygame.time.get_ticks()
		keys = pygame.key.get_pressed()
		for touche in self.gc:
			if keys[touche] == 1:
				if self.gc[touche]['actif']:
					if maintenant >= self.gc[touche]['suivant']:
						self.gc[touche]['suivant'] = self.gc[touche]['periode'] + maintenant
						pygame.event.post(pygame.event.Event(pygame.KEYPRESSED, {'key':touche}))
				else:
					self.gc[touche]['actif'] = True
					self.gc[touche]['suivant'] = self.gc[touche]['delai'] + maintenant
			else:
				self.gc[touche]['actif'] = False
				self.gc[touche]['suivant'] = 0

# Menu de sélection au début du jeu
class Menu():
	def __init__(self):
		self.police = pygame.font.Font("police/DTM-Mono.otf", 25)
		self.logo = pygame.image.load("images/ulgio.png")

		self.dernierCligno = 0
		self.visible = True

		self.dernierTemps = 0
		self.defile = 0

		pygame.mixer.music.load("sons/menu.ogg")
		pygame.mixer.music.play(-1)

	def dessiner_menu(self, tempsMaintenant):

		if self.defile < monde.mapSprite.get_width() - DIM_FENETRE[0]:
			self.defile -= 0.02 * (tempsMaintenant - self.dernierTemps)
			self.dernierTemps = tempsMaintenant

		FENETRE.blit(monde.mapSprite, [self.defile, 0])
		FENETRE.blit(self.logo, [DIM_FENETRE[0]//2 - self.logo.get_width()//2, 30])

		# Bouton Nouveau Jeu
		couleur = (255,255,255)
		bt1_txt = self.police.render("APPUYEZ SUR UNE [ENTER] POUR COMMENCER", True, couleur)
		taille_bt1 =  [bt1_txt.get_width(), bt1_txt.get_height()]

		if self.dernierCligno > 30:
			self.dernierCligno = 0
			self.visible = not self.visible
		else:
			self.dernierCligno += 1

		if self.visible:
			FENETRE.blit(bt1_txt, (DIM_FENETRE[0]//2 - taille_bt1[0]//2, DIM_FENETRE[1]//10 * 9 + 10))

	def entrer(self):
		SON_CLIC.play()
		initialiserJeu()

# Fonctions d'initialisation globale ---------------------------------------------
def retourMenu():
	global MENU_EN_COURS, menu
	monde.mapSprite = pygame.image.load("images/map_1.png")
	menu.defile = 0
	menu.dernierTemps = pygame.time.get_ticks()
	pygame.mixer.music.stop()
	pygame.mixer.music.load("sons/menu.ogg")
	pygame.mixer.music.play(-1)
	NIVEAU = 1
	MENU_EN_COURS = True

def initialiserJeu():
	global MENU_EN_COURS, NIVEAU, dialManager, monde, temps_precedent, premierTour, dialManager

	if not NIVEAU:
		monde.joueur = Entite([64,416], "joueur")
		monde.entites.append(Entite([6400,250], "porte"))
		monde.entites.append(monde.joueur)

		NIVEAU = 1
	else:
		monde.initMonde()
		monde.entites = []
		monde.joueur = Entite([63,416], "joueur")
		monde.entites.append(Entite([6400,250], "porte"))
		monde.entites.append(monde.joueur)

		temps_precedent = 0
		premierTour = True
		dialManager = DialManager(dialogues.LISTE)

		if NIVEAU == 2:
			NIVEAU = 1
			monde.etape = 0
			monde.chronoEtape = 0
			monde.map = maps.MAP_1
			monde.mapSprite = pygame.image.load("images/map_1.png")
			monde.dimCalque = (len(monde.map[0])*32, len(monde.map)*32)
			monde.calqueJeu = pygame.Surface(monde.dimCalque)


	MENU_EN_COURS = False

	if not monde.debug:
		pygame.mixer.music.stop()
		pygame.mixer.music.load("sons/overworld.ogg")
		pygame.mixer.music.play(-1)

# Variables globales ---------------------------------------------
MENU_EN_COURS = True
REINIT_EN_COURS = 0
NIVEAU = 0
EN_JEU = True
IPS = 60
DIM_FENETRE = (800,512)
FENETRE = pygame.display.set_mode(DIM_FENETRE)

# Pygame ---------------------------------------------------------
pygame.font.init()

pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.mixer.init()
pygame.init()
pygame.KEYPRESSED = pygame.USEREVENT
pygame.display.set_caption('ULGio')

# Bibliothèque sonore --------------------------------------------
SON_PIECE = pygame.mixer.Sound("sons/piece.ogg")
SON_PAUSE = pygame.mixer.Sound("sons/pause.wav")
SON_GAMEOVER = pygame.mixer.Sound("sons/mort.ogg")
SON_PIECE_ATTRAPE = pygame.mixer.Sound("sons/get_coin.wav")
SON_CHAMPI = pygame.mixer.Sound("sons/1-up.wav")
SON_SAUT = pygame.mixer.Sound("sons/saut.ogg")
SON_SPRING = pygame.mixer.Sound("sons/spring_saut.ogg")
SON_ECRASE = pygame.mixer.Sound("sons/kick.wav")
SON_CLIC = pygame.mixer.Sound("sons/clic.wav")
SON_MOT = pygame.mixer.Sound("sons/mot.ogg")
SON_DOULEUR_1 = pygame.mixer.Sound("sons/aie_1.wav")
SON_DOULEUR_2 = pygame.mixer.Sound("sons/aie_2.wav")
SON_DOULEUR_3 = pygame.mixer.Sound("sons/aie_2.wav")
SON_PILIER = pygame.mixer.Sound("sons/pilier.wav")
FLAPPY_RIRE = pygame.mixer.Sound("sons/rire2.ogg")
FLAPPY_PONDRE = pygame.mixer.Sound("sons/pondre.wav")
SON_BYEFLAPPY = pygame.mixer.Sound("sons/byeflappy.wav")
SON_VICTOIRE = pygame.mixer.Sound("sons/victoire.ogg")

# Variables en lien avec Pygame ---------------------------------
temps = pygame.time.Clock()

# Initialisation des objets de base ------------------------------
menu = Menu()
interface = Interface()
monde = Monde()
dialManager = DialManager(dialogues.LISTE)

gestionEntrees = GestionEntrees()

temps_precedent = 0
premierTour = True

while EN_JEU:
	gestionEntrees.traite_entrees()

	if MENU_EN_COURS:
		menu.dessiner_menu(pygame.time.get_ticks())

	if not MENU_EN_COURS and not NIVEAU == 0:
		tempsMaintenant = pygame.time.get_ticks()

		if monde.joueur.estMort and pygame.time.get_ticks() >= REINIT_EN_COURS:
			retourMenu()
			REINIT_EN_COURS = 0

		if premierTour:
			temps_precedent = tempsMaintenant
			premierTour = False

		if not dialManager.dialogueEnCours:
			monde.moteurPhysique(temps_precedent, tempsMaintenant)
			monde.collisionInterEntites()
			monde.monstreSpawner()
			monde.poubelleEntites()
		temps_precedent = tempsMaintenant

		monde.afficheMonde()
		interface.afficheInterface()
		for entite in monde.entites:
			if not dialManager.dialogueEnCours:
				entite.animeSprites(tempsMaintenant)

		dialManager.dialogue_event(monde.joueur.position[0])
		if dialManager.dialogueEnCours:
			dialManager.afficheCaseDialogue()
			dialManager.afficheDialogue(tempsMaintenant)

		if monde.changeMapChrono and tempsMaintenant > monde.changeMapChrono:
			monde.changeMap()
			monde.changeMapChrono = 0

		if NIVEAU == 2:
			monde.histoire()
			if monde.etape >= 7 and not dialManager.dialogueEnCours:
				monde.flappy().gestionOeufs(tempsMaintenant)
				monde.gestionPoofs()
				monde.joueur.gestionoeufTenu()

	temps.tick(IPS)
	pygame.display.flip()

pygame.display.quit()
pygame.quit()
exit()
