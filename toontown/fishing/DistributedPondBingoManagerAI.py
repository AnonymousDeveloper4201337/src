from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from toontown.fishing import BingoGlobals
from toontown.fishing import FishGlobals
from toontown.toonbase import ToontownGlobals
from toontown.fishing.NormalBingo import NormalBingo
from toontown.fishing.ThreewayBingo import ThreewayBingo
from toontown.fishing.DiagonalBingo import DiagonalBingo
from toontown.fishing.BlockoutBingo import BlockoutBingo
from toontown.fishing.FourCornerBingo import FourCornerBingo
from otp.ai.MagicWordGlobal import *
from direct.task import Task
from direct.distributed.ClockDelta import *
import random
RequestCard = {}


class DistributedPondBingoManagerAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory("DistributedPondBingoManagerAI")

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)
        self.air = air
        self.bingoCard = None
        self.tileSeed = None
        self.typeId = None
        self.state_ = 'Off'
        self.canCall = False
        self.shouldStop = False
        self.lastUpdate = globalClockDelta.getRealNetworkTime()
        self.cardId = 0

    def setPondDoId(self, pondId):
        self.pond = self.air.doId2do[pondId]

    def getPondDoId(self):
        return self.pond.getDoId()

    def updateGameState(self, gameState, cellId):
        pass

    def setCardState(self, cardId, typeId, tileSeed, gameState):
        pass

    def setState(self, state, timeStamp):
        pass

    def cardUpdate(self, cardId, cellId, genus, species):
        avId = self.air.getAvatarIdFromSender()
        spot = self.pond.hasToon(avId)
        if not spot:
            self.air.writeServerEvent('suspicious', avId, 'Toon tried to call bingo while not fishing!')
            return
        fishTuple = (genus, species)
        if (genus != spot.lastFish[1] or species != spot.lastFish[2]) and (spot.lastFish[0] != FishGlobals.BootItem):
            self.air.writeServerEvent('suspicious', avId, 'Toon tried to update bingo card with a fish they didn\'t catch!')
            return
        if cardId != self.cardId:
            self.air.writeServerEvent('suspicious', avId, 'Toon tried to update expired bingo card!')
            return
        if self.state_ != 'Playing':
            self.air.writeServerEvent('suspicious', avId, 'Toon tried to update while the game is not running!')
            return
        spot.lastFish = [None, None, None, None]
        result = self.bingoCard.cellUpdateCheck(cellId, genus, species)
        if result == BingoGlobals.WIN:
            self.canCall = True
            self.sendCanBingo()
            self.sendGameStateUpdate(cellId)
        elif result == BingoGlobals.UPDATE:
            self.sendGameStateUpdate(cellId)

    def enableBingo(self):
        createGame()

    def d_enableBingo(self):
        self.sendUpdate('enableBingo', [])

    def handleBingoCall(self, cardId):
        avId = self.air.getAvatarIdFromSender()
        spot = self.pond.hasToon(avId)
        if not spot:
            self.air.writeServerEvent('suspicious', avId, 'Toon tried to call bingo while not fishing!')
            return
        if not self.canCall:
            self.air.writeServerEvent('suspicious', avId, 'Toon tried to call bingo whle the game is not running!')
            return
        if cardId != self.cardId:
            self.air.writeServerEvent('suspicious', avId, 'Toon tried to call bingo with an expired cardId!')
            return
        av = self.air.doId2do[avId]
        av.d_announceBingo()
        self.rewardAll()

    def setJackpot(self, jackpot):
        self.jackpot = jackpot

    def d_setJackpot(self, jackpot):
        self.sendUpdate('setJackpot', [jackpot])

    def b_setJackpot(self, jackpot):
        self.setJackpot(jackpot)
        self.d_setJackpot(jackpot)

    def activateBingoForPlayer(self, avId):
        self.sendUpdateToAvatarId(avId, 'setCardState', [self.cardId, self.typeId, self.tileSeed, self.bingoCard.getGameState()])
        self.sendUpdateToAvatarId(avId, 'setState', [self.state_, self.lastUpdate])
        self.canCall = True

    def sendStateUpdate(self):
        self.lastUpdate = globalClockDelta.getRealNetworkTime()
        for spot in self.pond.spots:
            if self.pond.spots[spot].avId == None or self.pond.spots[spot].avId == 0:
                continue
            avId = self.pond.spots[spot].avId
            self.sendUpdateToAvatarId(avId, 'setState', [self.state_, self.lastUpdate])

    def sendCardStateUpdate(self):
        for spot in self.pond.spots:
            if self.pond.spots[spot].avId == None or self.pond.spots[spot].avId == 0:
                continue
            avId = self.pond.spots[spot].avId
            self.sendUpdateToAvatarId(avId, 'setCardState', [self.cardId, self.typeId, self.tileSeed, self.bingoCard.getGameState()])

    def sendGameStateUpdate(self, cellId):
        for spot in self.pond.spots:
            if self.pond.spots[spot].avId == None or self.pond.spots[spot].avId == 0:
                continue
            avId = self.pond.spots[spot].avId
            self.sendUpdateToAvatarId(avId, 'updateGameState', [self.bingoCard.getGameState(), cellId])

    def sendCanBingo(self):
        for spot in self.pond.spots:
            if self.pond.spots[spot].avId == None or self.pond.spots[spot].avId == 0:
                continue
            avId = self.pond.spots[spot].avId
            self.sendUpdateToAvatarId(avId, 'enableBingo', [])

    def rewardAll(self):
        self.state_ = 'Reward'
        self.sendStateUpdate()
        for spot in self.pond.spots:
            if self.pond.spots[spot].avId == None or self.pond.spots[spot].avId == 0:
                continue
            av = self.air.doId2do[self.pond.spots[spot].avId]
            av.addMoney(self.jackpot)
        if self.shouldStop:
            self.stopGame()
            return
        taskMgr.doMethodLater(5, DistributedPondBingoManagerAI.startWait, 'startWait%d' % self.getDoId(), [self])
        taskMgr.remove('finishGame%d' % self.getDoId())



    def finishGame(self):
        self.state_ = 'GameOver'
        self.sendStateUpdate()
        if self.shouldStop:
            self.stopGame()
            return
        taskMgr.doMethodLater(5, DistributedPondBingoManagerAI.startWait, 'startWait%d' % self.getDoId(), [self])

    def stopGame(self):
        self.state_ = 'CloseEvent'
        self.sendStateUpdate()
        taskMgr.doMethodLater(10, DistributedPondBingoManagerAI.turnOff, 'turnOff%d' % self.getDoId(), [self])

    def turnOff(self):
        self.state_ = 'Off'
        self.sendStateUpdate()

    def startIntermission(self):
        self.state_ = 'Intermission'
        self.sendStateUpdate()
        taskMgr.doMethodLater(300, DistributedPondBingoManagerAI.startWait, 'startWait%d' % self.getDoId(), [self])

    def startWait(self):
        self.state_ = 'WaitCountdown'
        self.sendStateUpdate()
        taskMgr.doMethodLater(15, DistributedPondBingoManagerAI.createGame, 'createGame%d' % self.getDoId(), [self])

    def createGame(self):
        self.canCall = False
        self.tileSeed = None
        self.typeId = None
        self.cardId += 1
        for spot in self.pond.spots:
            avId = self.pond.spots[spot].avId
            request = RequestCard.get(avId)
            if request:
                self.typeId, self.tileSeed = request
                del RequestCard[avId]
        if self.cardId > 65535:
            self.cardId = 0
        if not self.tileSeed:
            self.tileSeed = random.randrange(0, 65535)
        if self.typeId == None:
            self.typeId = random.randrange(0, 4)
        if self.typeId == BingoGlobals.NORMAL_CARD:
            self.bingoCard = NormalBingo()
        elif self.typeId == BingoGlobals.DIAGONAL_CARD:
            self.bingoCard = DiagonalBingo()
        elif self.typeId == BingoGlobals.THREEWAY_CARD:
            self.bingoCard = ThreewayBingo()
        elif self.typeId == BingoGlobals.FOURCORNER_CARD:
            self.bingoCard = FourCornerBingo()
        else:
            self.bingoCard = BlockoutBingo()
        self.bingoCard.generateCard(self.tileSeed, self.pond.getArea())
        self.sendCardStateUpdate()
        self.b_setJackpot(BingoGlobals.getJackpot(self.typeId))
        self.state_ = 'Playing'
        self.sendStateUpdate()
        taskMgr.doMethodLater(BingoGlobals.getGameTime(self.typeId), DistributedPondBingoManagerAI.finishGame, 'finishGame%d' % self.getDoId(), [self])
