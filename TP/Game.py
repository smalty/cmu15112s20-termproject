from direct.showbase.ShowBase import ShowBase
from panda3d.core import Vec3, Vec2
from panda3d.core import Plane, Point3
from direct.actor.Actor import Actor
from panda3d.core import CollisionSphere, CollisionNode
from panda3d.core import CollisionTraverser
from panda3d.core import CollisionHandlerPusher
from panda3d.core import CollisionTube
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import TextNode
import math
import random

#Name:Edric Eun
#Andrew ID:eeun

#Define general game object
class GameObject():
    def __init__(self, pos, modelName, modelAnims, maxHealth, maxSpeed, \
        jumpVel, colliderName):
        #Load model, velocity, max speed, health
        self.actor = Actor(modelName, modelAnims)
        self.actor.setScale(0.005, 0.005, 0.005)
        self.actor.reparentTo(render)
        self.actor.setPos(pos)
        self.health = maxHealth
        self.maxHealth = maxHealth
        self.maxSpeed = maxSpeed
        self.jumpVel = jumpVel
        self.velocity = Vec3(0, 0, 0)
        self.initialPos = pos

        #Set gravitational acceleration
        self.gravity = 20
        
        #Model is not jumping or walking currently
        self.walking = False
        self.jumping = False

        #Create a collider node on model with the given collider tag
        colliderNode = CollisionNode(colliderName)
        colliderNode.addSolid(CollisionSphere(0, 0, 300, 300))
        self.collider = self.actor.attachNewNode(colliderNode)

        #Show collider solid

        self.collider.setPythonTag('object', self)

    #Update game object
    def update(self, dt):
        if self.actor != None:
            velocity2D = self.velocity.getXy()

            #Set the speed to max speed if it is over the max speed
            speed = velocity2D.length()
            if speed > self.maxSpeed:
                self.velocity.normalize()
                self.velocity = self.velocity * self.maxSpeed

            #Use gravity acceleration on z component
            gravityVal = self.gravity * dt
            self.velocity.setZ(self.velocity.getZ() - gravityVal)

            self.actor.setPos(self.actor.getPos() + self.velocity * dt)

            #Makes sure actor does not fall below 0 in z axis
            if self.actor.getZ() < 0:
                self.actor.setZ(0)

    #Method to update health of object, but not exceed max health
    def updateHealth(self, dHealth):
        self.health += dHealth

        if self.health > self.maxHealth:
            self.health = self.maxHealth

    #Remove the python tag and the collider
    def clearTag(self):
        self.collider.clearPythonTag('object')
        base.cTrav.removeCollider(self.collider)
        base.pusher.removeCollider(self.collider)

        self.actor.cleanup()
        self.actor.removeNode()
        self.actor = None

        self.collider = None

#Player superclass from GameObject
class Player(GameObject):
    def __init__(self):
        GameObject.__init__(self, Vec3(0, 0, 0), 'models/panda-model', {
                                  'walk' : 'models/panda-walk4'
                              }, 
                              5, 
                              10, 
                              15, 
                              'player')
        self.yVector = Vec2(0, -1)

        #Damage is 1
        self.damage = 1
        
        #Set initial score to 0
        self.score = 0

        #Has no knife yet
        self.knife = None

        #Delay of knife
        self.knifeTimer = 1

        #Set mouse position to (0, 0)
        self.lastMousePos = Vec2(0, 0)

        #Create empty point of mouse position
        self.mousePos3D = Point3()

        #Add collider to base game
        base.pusher.addCollider(self.collider, self.actor)
        base.cTrav.addCollider(self.collider, base.pusher)

        #Create Health bar
        self.healthIcon = []
        
        for i in range(self.health):
            icon = OnscreenImage(image = 'UIHere.png', \
                pos = (-1.275 + i*0.075, 0, 0.95), scale = 0.04)
            icon.setTransparency(True)
            self.healthIcon.append(icon)
        
        self.scoreUI = OnscreenText(text = '', pos = (1.3, 0.9), mayChange = True, \
            align = TextNode.ARight)

    #If the self.health is updated, update the health icon
    def updateHealthUI(self):
        for index, icon in enumerate(self.healthIcon):
            if index < self.health:
                icon.show()
            else:
                icon.hide()
    
    def updateHealth(self, dHealth):
        GameObject.updateHealth(self, dHealth)
        self.updateHealthUI()


    def update(self, keys, dt):
        GameObject.update(self, dt)
        self.updateHealthUI()
        self.updateScoreUI()

        #Gets the mouse position (2D vector)
        mouseWatcher = base.mouseWatcherNode
        if mouseWatcher.hasMouse():
            mousePos = mouseWatcher.getMouse()
        else:
            mousePos = self.lastMousePos

        #Create 3D vector
        self.mousePos3D.setX(mousePos.getX())
        self.mousePos3D.setY(mousePos.getY())
        self.mousePos3D.setZ(self.actor.getZ())

        #Add time to the timer
        self.knifeTimer += dt

        velocity2D = self.velocity.getXy()
        
        #Set the direction the actor is facing to the direction of velocity
        if velocity2D != (0, 0):
            velocity2D.normalize()
            heading = self.yVector.signedAngleDeg(velocity2D)
            self.actor.setH(heading)
        else:
            self.walking = False

        #Update velocity depending on key pressed
        if keys['up']:
            self.walking = True
            self.velocity.setY(self.maxSpeed)

        if keys['down']:
            self.walking = True
            self.velocity.setY(-self.maxSpeed)

        if keys['left']:
            self.walking = True
            self.velocity.setX(-self.maxSpeed)

        if keys['right']:
            self.walking = True
            self.velocity.setX(self.maxSpeed)
        
        if not keys['up'] and not keys['down']:
            self.velocity.setY(0)
        
        if not keys['right'] and not keys['left']:
            self.velocity.setX(0)

        if keys['jump']:
            self.jumping = True
            if self.actor.getZ() == 0:
                self.velocity.setZ(self.jumpVel)

        if not keys['jump']:
            self.jumping = False
        
        #If shoot is true and the timer has passed, then shoot a knife towards mouse position.
        #If a knife is already out, clear that knife and shoot a new one
        if not isinstance(self, ThreeKnifePlayer):
            if keys['shoot']:
                if self.knifeTimer >= 1:
                    if self.knife != None:
                        self.knife.clearTag()
                        self.knife = Knife(20, self.actor.getPos(), self.mousePos3D, 1, \
                            'knife')
                        self.knifeTimer = 0
                    else:
                        self.knife = Knife(20, self.actor.getPos(), self.mousePos3D, 1, \
                            'knife')
                        self.knifeTimer = 0
        
        #Update the knife position
        if self.knife != None:
            self.knife.update(dt)
            
        #If actor is walking, use walking animation
        if self.walking:
            walkControl = self.actor.getAnimControl('walk')
            if not walkControl.isPlaying() and not self.jumping:
                self.actor.loop('walk')

        #Else, stop walk animation
        else:
            walkControl = self.actor.getAnimControl('walk')
            if walkControl.isPlaying():
                self.actor.stop('walk')

    #Updates the score
    def updateScore(self, dScore):
        self.score += dScore
        self.updateScoreUI()
    
    def updateScoreUI(self):
        self.scoreUI.setText(f'{base.player.score}')

    def cleanup(self):
        self.scoreUI.removeNode()
        for icon in self.healthIcon:
            icon.removeNode()

#A player that can shoot three knives at once
class ThreeKnifePlayer(Player):
    def __init__(self, startPos, health):
        Player.__init__(self)
        self.score = base.player.score
        self.health = health
        self.actor.setPos(startPos)

        self.knife1 = None
        self.knife2 = None
        self.knife3 = None

    def update(self, keys, dt):
        Player.update(self, keys, dt)
        
        #Vector Rotation Formula(from internet)
        self.mousePos3D30DegCC = Point3(math.cos(math.pi/4) * self.mousePos3D.getX() - \
            math.sin(math.pi/4) * self.mousePos3D.getY(), math.sin(math.pi/4) * self.mousePos3D.getX() + \
                math.cos(math.pi/4) * self.mousePos3D.getY(), 0) - self.mousePos3D
        
        self.mousePos3D30DegC = Point3(math.cos(-math.pi/4) * self.mousePos3D.getX() - \
            math.sin(-math.pi/4) * self.mousePos3D.getY(), math.sin(-math.pi/4) * self.mousePos3D.getX() + \
                math.cos(-math.pi/4) * self.mousePos3D.getY(), 0) - self.mousePos3D

        #Shoot 3 knives at different angles
        if keys['shoot']:
            if self.knifeTimer >= 1:
                if self.knife1 != None:
                    self.knife1.clearTag()
                    self.knife2.clearTag()
                    self.knife3.clearTag()
                    self.knife1 = Knife(20, self.actor.getPos(), self.mousePos3D, 1, \
                        'knife')
                    self.knife2 = Knife(20, self.actor.getPos(), self.mousePos3D + self.mousePos3D30DegCC, \
                        1, 'knife')
                    self.knife3 = Knife(20, self.actor.getPos(), self.mousePos3D + self.mousePos3D30DegC, \
                        1, 'knife')
                    self.knifeTimer = 0
                else:
                    self.knife1 = Knife(20, self.actor.getPos(), self.mousePos3D, 1, \
                        'knife')
                    self.knife2 = Knife(20, self.actor.getPos(), self.mousePos3D + self.mousePos3D30DegCC, \
                        1, 'knife')
                    self.knife3 = Knife(20, self.actor.getPos(), self.mousePos3D + self.mousePos3D30DegC, \
                        1, 'knife')
                    self.knifeTimer = 0
        
        if self.knife1 != None:
            self.knife1.update(dt)
            self.knife2.update(dt)
            self.knife3.update(dt)

    def updateHealthUI(self):
        Player.updateHealthUI(self)

    def updateHealth(self, dHealth):
        Player.updateHealth(self, dHealth)
    
    def updateScore(self, dScore):
        Player.updateScore(self, dScore)
    
    def updateScoreUI(self):
        Player.updateScoreUI(self)

#Deal Double Damage super class
class DoubleDamagePlayer(Player):
    def __init__(self, startPos, health):
        Player.__init__(self)
        self.actor.setPos(startPos)
        self.damage = 2

    def update(self, keys, dt):
        Player.update(self, keys, dt)

    def updateHealthUI(self):
        Player.updateHealthUI(self)

    def updateHealth(self, dHealth):
        Player.updateHealth(self, dHealth)
    
    def updateScore(self, dScore):
        Player.updateScore(self, dScore)
    
    def updateScoreUI(self):
        Player.updateScoreUI(self)

#Enemy superclass from GameObject
class Enemy(GameObject):
    def __init__(self):
        GameObject.__init__(self, Vec3(0, 0, 0), 'models/panda-model', {
                                  'walk' : 'models/panda-walk4'
                              }, 
                              3, 
                              0, 
                              0, 
                              'enemy')
        self.yVector = Vec2(0, -1)

        base.pusher.addCollider(self.collider, self.actor)
        base.cTrav.addCollider(self.collider, base.pusher)
    
    #Removes the enemy if health turns to 0
    def update(self, dt):
        if self.actor != None:
            GameObject.update(self, dt)
            if self.health <= 0:
                base.deadEnemies.append(self)
                base.player.updateScore(10)
                randomInteger = random.randint(1, 2)
                #Enemy will randomly drop a powerup
                if randomInteger == 1:
                    ThreeKnifePowerUp(self.actor.getPos(), 'smiley', 'threeKnife')
                elif randomInteger == 2:
                    DoubleDamage(self.actor.getPos(), 'frowney', 'doubleDamage')
                self.clearTag()
        
#Walking Enemy superclass from Enemy class
class WalkingEnemy(Enemy):
    def __init__(self, pos):
        GameObject.__init__(self, pos, 'models/panda-model', {
                                  'walk' : 'models/panda-walk4'
                              }, 
                              3, 
                              6, 
                              0, 
                              'enemy')
        self.yVector = Vec2(0, -1)

        #Set the range for the enemy to follow after the player
        self.range = 10

        base.pusher.addCollider(self.collider, self.actor)
        base.cTrav.addCollider(self.collider, base.pusher)

    def update(self, player, dt):
        Enemy.update(self, dt)
        if self.actor != None:
            vectorToPlayer = player.actor.getPos() - self.actor.getPos()
        #Sets the speed to maxspeed toward the player if inside a certain range
            if vectorToPlayer.length() < self.range:
                vectorToPlayer.normalize()
                self.velocity = vectorToPlayer * self.maxSpeed
            
            if vectorToPlayer.length() >= self.range:
                self.velocity.__init__(0, 0, 0)
            
            #Turn the enemy towards player
            if self.velocity != (0, 0, 0):
                vectorToPlayer.normalize()
                heading = self.yVector.signedAngleDeg(vectorToPlayer.getXy())
                self.actor.setH(heading)
                self.walking = True
            else:
                self.walking = False

            #Use walking animation if walking
            if self.walking:
                walkControl = self.actor.getAnimControl('walk')
                if not walkControl.isPlaying() and not self.jumping:
                    self.actor.loop('walk')
            
            else:
                walkControl = self.actor.getAnimControl('walk')
                if walkControl.isPlaying():
                    self.actor.stop('walk')

#Knife class
class Knife():
    def __init__(self, maxSpeed, startPos, direction, damage, colliderName):
        self.model = loader.loadModel('frowney')
        self.model.reparentTo(render)
        self.maxSpeed = maxSpeed
        self.direction = direction
        self.damage = damage
        self.direction.normalize()
        self.yVector = Vec2(0, -1)
        velocity2D = self.direction.getXy()
        heading = self.yVector.signedAngleDeg(velocity2D)
        self.model.setH(heading)
        
        #Set the knife to spawn just a little in front of the player
        startingPosition = Vec3()
        startingPosition.setX(self.direction.getX())
        startingPosition.setY(self.direction.getY())
        startingPosition.setZ(2/5)

        self.model.setPos(base.player.actor.getPos() + startingPosition * 5)
        
        #Add collision nodes and solids to knife and base game
        colliderNode = CollisionNode(colliderName)

        colliderNode.addSolid(CollisionTube(0, 0, 0, self.direction.getX(), \
            self.direction.getY(), self.direction.getZ(), 0.5))

        self.collider = self.model.attachNewNode(colliderNode)

        self.collider.setPythonTag('knife', self)

        base.pusher.addCollider(self.collider, self.model)
        base.cTrav.addCollider(self.collider, base.pusher)

        self.velocity = self.direction * self.maxSpeed

        #Show collider for now

    #Knife travels towards mouse position. 
    #If knife is a certain distance away from the player, remove the knife
    def update(self, dt):
        if self.collider != None:
            self.model.setPos(self.model.getPos() + self.velocity * dt)
            distanceFromPlayer = self.model.getPos() - base.player.actor.getPos()
            if distanceFromPlayer.length() >= 10:
                self.clearTag()

    #Method to remove knife
    def clearTag(self):
        if self.collider != None and not self.collider.isEmpty():
            self.collider.clearPythonTag('knife')
            base.cTrav.removeCollider(self.collider)
            base.pusher.removeCollider(self.collider)

        self.model.removeNode()
            
        self.collider = None

#Class of Powerups
class PowerUp():
    def __init__(self, startPos, model, colliderName):
        self.model = loader.loadModel(model)
        self.model.setPos(startPos)
        self.model.reparentTo(render)

#Superclass of powerups that lets player shoot three knives
class ThreeKnifePowerUp(PowerUp):
    def __init__(self, startPos, model, colliderName):
        PowerUp.__init__(self, startPos, model, colliderName)

        colliderNode = CollisionNode(colliderName)
        colliderNode.addSolid(CollisionSphere(0, 0, 1, 1))

        self.collider = self.model.attachNewNode(colliderNode)

        base.pusher.addCollider(self.collider, self.model)
        base.cTrav.addCollider(self.collider, base.pusher)

        self.collider.setPythonTag('threeKnifePU', self)
    
    def clearTag(self):
        if self.collider != None and not self.collider.isEmpty():
            self.collider.clearPythonTag('threeKnifePU')
            base.cTrav.removeCollider(self.collider)
            base.pusher.removeCollider(self.collider)

        self.model.removeNode()
            
        self.collider = None

#Double damage powerup that does what it says
class DoubleDamage(PowerUp):
    def __init__(self, startPos, model, colliderName):
        PowerUp.__init__(self, startPos, model, colliderName)

        colliderNode = CollisionNode(colliderName)
        colliderNode.addSolid(CollisionSphere(0, 0, 1, 1))

        self.collider = self.model.attachNewNode(colliderNode)

        base.pusher.addCollider(self.collider, self.model)
        base.cTrav.addCollider(self.collider, base.pusher)

        self.collider.setPythonTag('DoubleDamagePU', self)

        self.range = 15

    def clearTag(self):
        if self.collider != None and not self.collider.isEmpty():
            self.collider.clearPythonTag('DoubleDamagePU')
            base.cTrav.removeCollider(self.collider)
            base.pusher.removeCollider(self.collider)

        self.model.removeNode()
            
        self.collider = None

#Final Boss class is a class of its own
class FinalBoss():
    def __init__(self, startPos, colliderName):
        self.health = 30
        self.actor = Actor('models/panda-model', {'walk' : 'models/panda-walk4'})
        self.actor.setScale(0.007, 0.007, 0.007)
        self.actor.setPos(startPos)
        self.actor.reparentTo(render)
        self.maxSpeed = 5
        self.range = 15
        self.yVector = Vec2(0, -1)
        self.velocity = Vec3(0, 0, 0)

        #Set the attack timer so it attacks every 3 sec
        self.attackTimer = 3
        
        #Add a timer to show that the boss is charging a fireball
        self.largeFireballTimer = 0

        self.damage = 2

        #The attack number. There are 3 options the boss can do
        self.attack = None

        self.fireball = None

        #At the last stage, instead of shooting 1 fireball, it shoots three
        self.fireball1 = None
        self.fireball2 = None
        self.fireball3 = None

        #Have a list of fireballs so it shoots out multiple fireballs
        self.fireballWave = []

        colliderNode = CollisionNode(colliderName)
        colliderNode.addSolid(CollisionSphere(0, 0, 300, 300))

        self.collider = self.actor.attachNewNode(colliderNode)

        base.pusher.addCollider(self.collider, self.actor)
        base.cTrav.addCollider(self.collider, base.pusher)

        self.collider.setPythonTag('finalBoss', self)
        

    def update(self, dt):
        #Same code as walking Enemy
        if self.actor != None:
            vectorToPlayerBoss = base.player.actor.getPos() - self.actor.getPos()
            if vectorToPlayerBoss.length() < self.range:
                vectorToPlayerBoss.normalize()
            self.velocity = vectorToPlayerBoss * self.maxSpeed
        
            if vectorToPlayerBoss.length() >= self.range:
                self.velocity.__init__(Vec3(0, 0, 0))
            
            vectorToPlayerBoss.normalize()
            heading = self.yVector.signedAngleDeg(vectorToPlayerBoss.getXy())
            self.actor.setH(heading)

            self.actor.setPos(self.actor.getPos() + self.velocity * dt)
        else:
            vectorToPlayerBoss = Vec3(0, 0, 0)
        
        #Update the fireballs
        if self.fireball != None:
            self.fireball.update(dt)
        
        if self.fireball1 != None:
            self.fireball1.update(dt)
        
        if self.fireball2 != None:
            self.fireball2.update(dt)

        if self.fireball3 != None:
            self.fireball3.update(dt)

        for fireball in self.fireballWave:
            if isinstance(fireball, Fireball):
                fireball.update(dt)

        if self.velocity != Vec3(0, 0, 0):
            self.walking = True
        else:
            self.walking = False
        
        #If it is walking start the boss fight
        if self.velocity != Vec3(0, 0, 0):
            #The first stage of the boss fight: if the health is between 20 to 30
            if self.health >= 20:
                self.maxSpeed = 5
                if self.attackTimer >= 3:
                    if self.attack != 3:
                        #Choose from 3 attacks. After attack is done, reset attack timer
                        self.attack = random.randint(1,3)
                        if self.attack == 1:
                            self.fireball = Fireball(10, 1, self.actor.getPos(), vectorToPlayerBoss, 'fireball')
                            self.attackTimer = 0
                        if self.attack == 2:
                            #Shoot a wave of fireballs(12) in a half circle aimed toward the player
                            for num in range(12):
                                self.fireballWave.append(Fireball(10, 1, self.actor.getPos(), \
                                    vectorAngleChange(vectorToPlayerBoss, num * math.pi/12 - math.pi/2), \
                                        'fireball'))
                            self.attackTimer = 0
                    #This attack requires the boss to stop and charge
                    elif self.attack == 3:
                        self.maxSpeed = 1
                        self.largeFireballTimer += dt
                        if self.largeFireballTimer >= 2:
                            self.fireball = Fireball(10, 2, self.actor.getPos(), \
                                vectorToPlayerBoss, 'fireball')
                            self.largeFireballTimer = 0
                            self.attack = 0
                            self.attackTimer = 0
                else:
                    self.attackTimer += dt
            #Second phase of the boss. Fireballs are now faster
            elif self.health >= 10:
                self.maxSpeed = 7
                if self.attackTimer >= 3:
                    if self.attack != 3:
                        self.attack = random.randint(1,3)
                        if self.attack == 1:
                            self.fireball = Fireball(15, 1, self.actor.getPos(), vectorToPlayerBoss, 'fireball')
                            self.attackTimer = 0
                        if self.attack == 2:
                            for num in range(12):
                                self.fireballWave.append(Fireball(15, 1, self.actor.getPos(), \
                                    vectorAngleChange(vectorToPlayerBoss, num * math.pi/12 - math.pi/2), \
                                        'fireball'))
                            self.attackTimer = 0
                    elif self.attack == 3:
                        self.maxSpeed = 1
                        self.largeFireballTimer += dt
                        if self.largeFireballTimer >= 1:
                            self.fireball = Fireball(15, 2, self.actor.getPos(), \
                                vectorToPlayerBoss, 'fireball')
                            self.largeFireballTimer = 0
                            self.attack = 0
                            self.attackTimer = 0
                else:
                    self.attackTimer += dt
            #Third stage: Boss is faster, shoots 3 fireballs instead of 1, 
            #shoots out a wave of 24 fireballs, and does not charge for 
            #large fireball
            elif self.health > 0:
                self.maxSpeed = 8
                if self.attackTimer >= 5:
                    self.attack = random.randint(1,3)
                    if self.attack == 1:
                        self.fireball1 = Fireball(20, 1, self.actor.getPos(), vectorToPlayerBoss, 'fireball')
                        self.fireball2 = Fireball(20, 1, self.actor.getPos(), \
                            vectorAngleChange(vectorToPlayerBoss, math.pi/4), 'fireball')
                        self.fireball3 = Fireball(20, 1, self.actor.getPos(), \
                            vectorAngleChange(vectorToPlayerBoss, -math.pi/4), 'fireball')
                        self.attackTimer = 0
                    if self.attack == 2:
                        for num in range(24):
                            self.fireballWave.append(Fireball(20, 1, self.actor.getPos(), \
                                    vectorAngleChange(vectorToPlayerBoss, num * math.pi/24 - math.pi/2), \
                                        'fireball'))
                        self.attackTimer = 0
                    if self.attack == 3:
                        self.maxSpeed = 1
                        self.fireball = Fireball(20, 2, self.actor.getPos(), vectorToPlayerBoss, 'fireball')
                        self.attackTimer = 0
                else:
                    self.attackTimer += dt
            elif self.health == 0:
                if self.actor != None:
                    base.player.updateScore(100)
                    self.clearTag()
    
    def updateHealth(self, dHealth):
        self.health += dHealth

    def clearTag(self):
        if self.collider != None:
            self.collider.clearPythonTag('finalBoss')
            base.cTrav.removeCollider(self.collider)
            base.pusher.removeCollider(self.collider)

        if self.actor != None:
            self.actor.cleanup()
            self.actor.removeNode()
            self.actor = None

        if self.fireball != None:
            self.fireball.clearTag()
        if self.fireball1 != None:
            self.fireball1.clearTag()
        if self.fireball2 != None:
            self.fireball2.clearTag()
        if self.fireball3 != None:
            self.fireball3.clearTag()
        for fireball in self.fireballWave:
            if fireball != None:
                fireball.clearTag()
        self.collider = None

#Fireball acts the same way as a knife but takes in scale as a parameter
class Fireball():
    def __init__(self, maxSpeed, scale, startPos, direction, colliderName):
        self.model = loader.loadModel('smiley')
        self.model.setScale(scale, scale, scale)
        self.model.reparentTo(render)
        self.maxSpeed = maxSpeed
        self.direction = direction
        self.direction.normalize()
        self.yVector = Vec2(0, -1)
        velocity2D = self.direction.getXy()
        heading = self.yVector.signedAngleDeg(velocity2D)
        self.model.setH(heading)

        startingPosition = Vec3()
        startingPosition.setX(self.direction.getX())
        startingPosition.setY(self.direction.getY())
        startingPosition.setZ(2/5)

        self.model.setPos(base.finalBoss.actor.getPos() + startingPosition * 5)

        colliderNode = CollisionNode(colliderName)
        colliderNode.addSolid(CollisionSphere(0, 0, 1, 1))

        self.collider = self.model.attachNewNode(colliderNode)

        self.collider.setPythonTag('fireball', self)

        base.pusher.addCollider(self.collider, self.model)
        base.cTrav.addCollider(self.collider, base.pusher)

        self.velocity = self.direction * self.maxSpeed


    def update(self, dt):
        if self.collider != None:
            self.model.setPos(self.model.getPos() + self.velocity * dt)
            distanceFromBoss = self.model.getPos() - base.finalBoss.actor.getPos()
            if distanceFromBoss.length() >= 20:
                self.clearTag()

    def clearTag(self):
        if self.collider != None and not self.collider.isEmpty():
            self.collider.clearPythonTag('knife')
            base.cTrav.removeCollider(self.collider)
            base.pusher.removeCollider(self.collider)

        self.model.removeNode()
            
        self.collider = None        
        
#Function that returns the vector rotated at the angle counterclockwise
def vectorAngleChange(vector, angle):
    return Point3(math.cos(angle) * vector.getX() - math.sin(angle) * vector.getY(), \
        math.sin(angle) * vector.getX() + math.cos(angle) * vector.getY(), 0)
