# Copyright (c) 2010-2013, Regents of the University of California. 
# All rights reserved. 
#  
# Released under the BSD 3-Clause license as published at the link below.
# https://openwsn.atlassian.net/wiki/display/OW/License
import logging
log = logging.getLogger('remoteConnector')
log.setLevel(logging.ERROR)
log.addHandler(logging.NullHandler())

import threading
import socket
import traceback
import sys
import openvisualizer.openvisualizer_utils as u
import zmq
import time

from openvisualizer.eventBus      import eventBusClient
from openvisualizer.moteState     import moteState


class remoteConnector(eventBusClient.eventBusClient):
    
    def __init__(self, iplist=[]):
        
        # log
        log.info("creating instance")

        # local variables
        self.stateLock                 = threading.Lock()
        self.networkPrefix             = None
        self._subcribedDataForDagRoot  = False
        self.iplist = iplist

        self.context = zmq.Context()
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.bind("tcp://*:50000")
        self.publisher.send('')
        print 'publisher started'


        # give this thread a name
        self.name = 'remoteConnector'
       
        eventBusClient.eventBusClient.__init__(
            self,
            name             = self.name,
            registrations =  [
                {
                    'sender'   : self.WILDCARD,
                    'signal'   : 'infoDagRoot',
                    'callback' : self._sendToRemote_handler,
                },
                {
                    'sender'   : self.WILDCARD,
                    'signal'   : 'cmdToMote',
                    'callback' : self._sendToRemote_handler,
                },
                {
                    'sender'   : self.WILDCARD,
                    'signal'   : 'bytesToMesh',
                    'callback' : self._sendToRemote_handler,
                }
            ]
        )
        
        # # subscribe to dispatcher
        # dispatcher.connect(
        #     self._sendToParser,
        #     signal = 'fromMoteProbe@'+self.serialport,
        # )
        
    # def _sendToParser(self,data):
    #
    #     input = data
    #
    #     # log
    #     if log.isEnabledFor(logging.DEBUG):
    #         log.debug("received input={0}".format(input))
    #
    #     # parse input
    #     try:
    #         (eventSubType,parsedNotif)  = self.parser.parseInput(input)
    #         assert isinstance(eventSubType,str)
    #     except ParserException.ParserException as err:
    #         # log
    #         log.error(str(err))
    #         pass
    #     else:
    #         # dispatch
    #         self.dispatch('fromMote.'+eventSubType,parsedNotif)
        
    #======================== eventBus interaction ============================
    
    def _sendToRemote_handler(self,sender,signal,data):

        self.publisher.send_json({'sender' : sender, 'signal' : signal, 'data':data})
        print 'msg sent'

        # # I only care about "infoDagRoot" notifications about my mote
        # if not data['serialPort']==self.roverMote:
        #     return
        #
        # with self.stateLock:
        #
        #     if   data['isDAGroot']==1 and (not self._subcribedDataForDagRoot):
        #         # this moteConnector is connected to a DAGroot
        #
        #         # connect to dispatcher
        #         self.register(
        #             sender   = self.WILDCARD,
        #             signal   = 'bytesToMesh',
        #             callback = self._bytesToMesh_handler,
        #         )
        #
        #         # remember I'm subscribed
        #         self._subcribedDataForDagRoot = True
        #
        #     elif data['isDAGroot']==0 and self._subcribedDataForDagRoot:
        #         # this moteConnector is *not* connected to a DAGroot
        #
        #         # disconnect from dispatcher
        #         self.unregister(
        #             sender   = self.WILDCARD,
        #             signal   = 'bytesToMesh',
        #             callback = self._bytesToMesh_handler,
        #         )
        #
        #         # remember I'm not subscribed
        #         self._subcribedDataForDagRoot = False
    

    
    # def _GDcommandToBytes(self,data):
    #
    #     outcome    = False
    #     dataToSend = []
    #
    #     # get imageId
    #     if data[0] == 'gd_root':
    #         imageId  = 1
    #     elif data[0] == 'gd_sniffer':
    #         imageId = 2
    #     else:
    #         print "============================================="
    #         print "Wrong Image ({0})! (Available: gd_root OR gd_sniffer)\n".format(data[0])
    #         return [outcome,dataToSend]
    #
    #     # get commandId
    #     commandIndex = 0
    #     for cmd in moteState.moteState.COMMAND_ALL:
    #         if data[1] == cmd[0]:
    #             commandId  = cmd[1]
    #             commandLen = cmd[2]
    #             break
    #         else:
    #             commandIndex += 1
    #
    #     # check avaliability of command
    #     if commandIndex == len(moteState.moteState.COMMAND_ALL):
    #         print "============================================="
    #         print "Wrong Command Type! Available Command Type: {"
    #         for cmd in moteState.moteState.COMMAND_ALL:
    #             print " {0}".format(cmd[0])
    #         print " }"
    #         return [outcome,dataToSend]
    #
    #     if data[1][:2] == '6p':
    #         try:
    #             dataToSend = [OpenParser.OpenParser.SERFRAME_PC2MOTE_COMMAND_GD,
    #                 2, # version
    #                 imageId,
    #                 commandId,
    #                 len(data[2][1:-1].split(','))
    #             ]
    #             if data[1] == '6pAdd' or data[1] == '6pDelete':
    #                 if len(data[2][1:-1].split(','))>0:
    #                     dataToSend += [int(i) for i in data[2][1:-1].split(',')] # celllist
    #         except:
    #             print "============================================="
    #             print "Wrong 6p parameter format {0}. Split the slot by".format(data[2])
    #             print "comma. e.g. 6,7. (up to 3)"
    #             return [outcome,dataToSend]
    #     else:
    #         parameter = int(data[2])
    #         if parameter <= 0xffff:
    #             parameter  = [(parameter & 0xff),((parameter >> 8) & 0xff)]
    #             dataToSend = [OpenParser.OpenParser.SERFRAME_PC2MOTE_COMMAND_GD,
    #                 2, # version
    #                 imageId,
    #                 commandId,
    #                 commandLen, # length
    #                 parameter[0],
    #                 parameter[1]
    #             ]
    #         else:
    #             # more than two bytes parameter, error
    #             print "============================================="
    #             print "Paramter Wrong! (Available: 0x0000~0xffff)\n"
    #             return [outcome,dataToSend]
    #
    #     # the command is legal if I got here
    #     outcome = True
    #     return [outcome,dataToSend]


    # def _bytesToMesh_handler(self,sender,signal,data):
    #     assert type(data)==tuple
    #     assert len(data)==2
    #
    #     (nextHop,lowpan) = data
    #
    #     self._sendToMoteProbe(
    #         dataToSend = [OpenParser.OpenParser.SERFRAME_PC2MOTE_DATA]+nextHop+lowpan,
    #     )
    
    #======================== public ==========================================
    
    def quit(self):
        raise NotImplementedError()

    def addRaspi(self, ip):
        self.iplist.append(ip)