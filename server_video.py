import av.logging
# monkey patch av.logging.restore_default_callback 
restore_default_callback = lambda *args: args
av.logging.restore_default_callback = restore_default_callback
av.logging.set_level(av.logging.ERROR)
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import pyqtSignal, QThread, Qt
from calls import Ui_MainWindow
from aiohttp import web
from aiohttp.web_runner import GracefulExit
from aiortc.mediastreams import MediaStreamTrack,MediaStreamError
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.rtcrtpsender import RTCRtpSender
from aiortc.contrib.media import MediaPlayer
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder, MediaRelay
import av
import pyaudio
from pydub import AudioSegment,effects,utils,generators
import asyncio
import json
import os
from multiprocessing import Process, Queue, Pipe, freeze_support
from queue import Queue as Simple_Queue
import sys
import threading
from datetime import datetime, timedelta
from time import sleep
import fractions
import time
import requests
import platform
from PIL import Image
import ssl
import logging
ssl._create_default_https_context = ssl._create_unverified_context 
from pyngrok import ngrok, conf
from pyngrok.conf import PyngrokConfig
from pyngrok import conf

from pygrabber.dshow_graph import FilterGraph
import traceback

#conf.set_default(PyngrokConfig(region="au", ngrok_path=os.path.abspath("ngrok.exe")))
ngrok.set_auth_token("1kxaH4jyih9qTuyTBE0V6bzYbnq_nVaCNY5wwUriYY5oiLDr")
import socket

stream_offer = None
pc = None
micTrack = None
blackHole = None

relay = None

ip_address = None

class Main:
	def __init__(self,ngrok_url):
		self.app = QtWidgets.QApplication(sys.argv)
		self.MainWindow = QtWidgets.QMainWindow()
		self.ui = Ui_MainWindow()
		self.ui.setupUi(self.MainWindow)
		self.MainWindow.showMaximized()
		
		
		self.ui.server_frame.hide()
		self.ui.client_1_frame.hide()
		self.ui.client_2_frame.hide()
		self.ui.client_3_frame.hide()
		
		self.ui.ngrok_url.setText(ngrok_url)

		self.mother_pipe, self.child_pipe = Pipe()
		self.call_1_queue = Queue()
		self.call_2_queue = Queue()
		self.call_3_queue = Queue()
		self.emitter = Emitter(self.mother_pipe)
		
		self.emitter.call_1_offering.connect(lambda name,surname:self.new_call_1(name,surname))
		self.emitter.call_1_status.connect(lambda status:self.call_1_status(status))
		
		self.emitter.call_2_offering.connect(lambda name,surname:self.new_call_2(name,surname))
		self.emitter.call_2_status.connect(lambda status:self.call_2_status(status))

		self.emitter.call_3_offering.connect(lambda name,surname:self.new_call_3(name,surname))
		self.emitter.call_3_status.connect(lambda status:self.call_3_status(status))
		
		self.emitter.server_web_camera_packet.connect(lambda pil_image:self.server_web_camera_packet(pil_image[0]))
		self.emitter.client_1_web_camera_packet.connect(lambda pil_image:self.client_1_web_camera_packet(pil_image[0]))
		self.emitter.client_2_web_camera_packet.connect(lambda pil_image:self.client_2_web_camera_packet(pil_image[0]))
		self.emitter.client_3_web_camera_packet.connect(lambda pil_image:self.client_3_web_camera_packet(pil_image[0]))
		self.emitter.hide_server_web_camera.connect(lambda:self.hide_server_web_camera())
		self.emitter.start()		
		
		self.aiohttp_server = WebRtcServer(self.child_pipe,self.call_1_queue,self.call_2_queue,self.call_3_queue)
		self.aiohttp_server.start()
		
		self.MainWindow.closeEvent = lambda event:self.closeEvent(event)
		
		sys.exit(self.app.exec_())

	def new_call_1(self,name,surname):
		self.ui.client_1_frame.show()
		
		self.ui.client_1_label.show()
		self.ui.client_1_label.setText("Τηλεφωνική κλήση από: "+str(name)+" "+str(surname))
		
		self.ui.client_1_accept.show()
		self.ui.client_1_accept.clicked.connect(lambda state:self.answer_call_1(state))
		
		self.ui.client_1_video.clear()
		
		self.ui.client_1_reject.show()
		self.ui.client_1_reject.clicked.connect(lambda state:self.reject_call_1(state))
		
		self.ui.client_1_stop.hide()
	
	def answer_call_1(self,state):
		self.ui.client_1_accept.hide()
		self.ui.client_1_reject.hide()
		self.ui.client_1_stop.show()
		self.ui.client_1_stop.clicked.connect(lambda state:self.end_call_1(state))
		self.call_1_queue.put({"type":"call-1","call":"answer"})
		
	def reject_call_1(self,state):
		self.ui.client_1_frame.hide()
		self.ui.client_1_label.hide()
		self.ui.client_1_accept.hide()
		self.ui.client_1_reject.hide()
		self.ui.client_1_stop.hide()
		self.call_1_queue.put({"type":"call-1","call":"reject"})
		
	def end_call_1(self,state):
		self.ui.client_1_frame.hide()
		self.ui.client_1_label.hide()
		self.ui.client_1_accept.hide()
		self.ui.client_1_reject.hide()
		self.ui.client_1_stop.hide()
		self.call_1_queue.put({"type":"call-1","call":"end"})
	
	def call_1_status(self,status):
		if status == "closed-by-client" or status == "closed-by-server":
			self.ui.client_1_frame.hide()
			self.ui.client_1_label.hide()
			self.ui.client_1_accept.hide()
			self.ui.client_1_reject.hide()
			self.ui.client_1_stop.hide()





	def new_call_2(self,name,surname):
		self.ui.client_2_frame.show()
		
		self.ui.client_2_label.show()
		self.ui.client_2_label.setText("Τηλεφωνική κλήση από: "+str(name)+" "+str(surname))
		
		self.ui.client_2_accept.show()
		self.ui.client_2_accept.clicked.connect(lambda state:self.answer_call_2(state))
		
		self.ui.client_2_reject.show()
		self.ui.client_2_reject.clicked.connect(lambda state:self.reject_call_2(state))
		
		self.ui.client_2_video.clear()
		
		self.ui.client_2_stop.hide()
	
	def answer_call_2(self,state):
		self.ui.client_2_accept.hide()
		self.ui.client_2_reject.hide()
		self.ui.client_2_stop.show()
		self.ui.client_2_stop.clicked.connect(lambda state:self.end_call_2(state))
		self.call_2_queue.put({"type":"call-2","call":"answer"})
		
	def reject_call_2(self,state):
		self.ui.client_2_frame.hide()
		self.ui.client_2_label.hide()
		self.ui.client_2_accept.hide()
		self.ui.client_2_reject.hide()
		self.ui.client_2_stop.hide()
		self.call_2_queue.put({"type":"call-2","call":"reject"})
		
	def end_call_2(self,state):
		self.ui.client_2_frame.hide()
		self.ui.client_2_label.hide()
		self.ui.client_2_accept.hide()
		self.ui.client_2_reject.hide()
		self.ui.client_2_stop.hide()
		self.call_2_queue.put({"type":"call-2","call":"end"})
	
	def call_2_status(self,status):
		if status == "closed-by-client" or status == "closed-by-server":
			self.ui.client_2_frame.hide()
			self.ui.client_2_label.hide()
			self.ui.client_2_accept.hide()
			self.ui.client_2_reject.hide()
			self.ui.client_2_stop.hide()






	def new_call_3(self,name,surname):
		self.ui.client_3_frame.show()
		
		self.ui.client_3_label.show()
		self.ui.client_3_label.setText("Τηλεφωνική κλήση από: "+str(name)+" "+str(surname))
		
		self.ui.client_3_accept.show()
		self.ui.client_3_accept.clicked.connect(lambda state:self.answer_call_3(state))
		
		self.ui.client_3_reject.show()
		self.ui.client_3_reject.clicked.connect(lambda state:self.reject_call_3(state))
		
		self.ui.client_3_video.clear()
		
		self.ui.client_3_stop.hide()
	
	def answer_call_3(self,state):
		self.ui.client_3_accept.hide()
		self.ui.client_3_reject.hide()
		self.ui.client_3_stop.show()
		self.ui.client_3_stop.clicked.connect(lambda state:self.end_call_3(state))
		self.call_3_queue.put({"type":"call-3","call":"answer"})
		
	def reject_call_3(self,state):
		self.ui.client_3_frame.hide()
		self.ui.client_3_label.hide()
		self.ui.client_3_accept.hide()
		self.ui.client_3_reject.hide()
		self.ui.client_3_stop.hide()
		self.call_3_queue.put({"type":"call-3","call":"reject"})
		
	def end_call_3(self,state):
		self.ui.client_3_frame.hide()
		self.ui.client_3_label.hide()
		self.ui.client_3_accept.hide()
		self.ui.client_3_reject.hide()
		self.ui.client_3_stop.hide()
		self.call_3_queue.put({"type":"call-3","call":"end"})
	
	def call_3_status(self,status):
		if status == "closed-by-client" or status == "closed-by-server":
			self.ui.client_3_frame.hide()
			self.ui.client_3_label.hide()
			self.ui.client_3_accept.hide()
			self.ui.client_3_reject.hide()
			self.ui.client_3_stop.hide()

	
	def server_web_camera_packet(self,pil_image):
		self.ui.server_frame.show()
		pixmap = self.pil2pixmap(pil_image)
		self.ui.server_video.setPixmap(pixmap)
		self.ui.server_video.show()
	
	def client_1_web_camera_packet(self,pil_image):
		if pil_image is None:
			return self.end_call_1(None)
		pixmap = self.pil2pixmap(pil_image)
		self.ui.client_1_video.setPixmap(pixmap)
		self.ui.client_1_video.show()

	def client_2_web_camera_packet(self,pil_image):
		if pil_image is None:
			return self.end_call_2(None)
		pixmap = self.pil2pixmap(pil_image)
		self.ui.client_2_video.setPixmap(pixmap)
		self.ui.client_2_video.show()
		
	def client_3_web_camera_packet(self,pil_image):
		if pil_image is None:
			return self.end_call_3(None)
		pixmap = self.pil2pixmap(pil_image)
		self.ui.client_3_video.setPixmap(pixmap)
		self.ui.client_3_video.show()

	def pil2pixmap(self, im):

		if im.mode == "RGB":
			r, g, b = im.split()
			im = Image.merge("RGB", (b, g, r))
		elif  im.mode == "RGBA":
			r, g, b, a = im.split()
			im = Image.merge("RGBA", (b, g, r, a))
		elif im.mode == "L":
			im = im.convert("RGBA")
		# Bild in RGBA konvertieren, falls nicht bereits passiert
		im2 = im.convert("RGBA")
		data = im2.tobytes("raw", "RGBA")
		qim = QtGui.QImage(data, im.size[0], im.size[1], QtGui.QImage.Format_ARGB32)
		pixmap = QtGui.QPixmap.fromImage(qim)
		return pixmap

	def hide_server_web_camera(self):
		self.ui.server_video.clear()
		self.ui.server_frame.hide()

	
	def closeEvent(self,event):
		#try:
		#	response = requests.post('http://192.168.1.188:8080/shutdown', timeout=30)
		#except:
		#	pass
		os.system("taskkill /f /im ngrok.exe")
		self.aiohttp_server.terminate()
		event.accept()

class Emitter(QThread):
	call_1_offering = pyqtSignal(str,str)
	call_1_status = pyqtSignal(str)

	call_2_offering = pyqtSignal(str,str)
	call_2_status = pyqtSignal(str)

	call_3_offering = pyqtSignal(str,str)
	call_3_status = pyqtSignal(str)
	
	hide_server_web_camera = pyqtSignal()


	server_web_camera_packet = pyqtSignal(list)
	client_1_web_camera_packet = pyqtSignal(list)
	client_2_web_camera_packet = pyqtSignal(list)
	client_3_web_camera_packet = pyqtSignal(list)
	
	def __init__(self, from_process: Pipe):
		super().__init__()
		self.data_from_process = from_process
		
	def run(self):
		while True:
			data = self.data_from_process.recv()
			if data["type"]=="call_1_offering":
				self.call_1_offering.emit(data["name"],data["surname"])
			elif data["type"] == "call-1-status":
				self.call_1_status.emit(data["status"])
			elif data["type"]=="call_2_offering":
				self.call_2_offering.emit(data["name"],data["surname"])
			elif data["type"] == "call-2-status":
				self.call_2_status.emit(data["status"])
			elif data["type"]=="call_3_offering":
				self.call_3_offering.emit(data["name"],data["surname"])
			elif data["type"] == "call-3-status":
				self.call_3_status.emit(data["status"])
			elif data["type"] == "server-web-camera-frame":
				self.server_web_camera_packet.emit(data["pil_image"])
			elif data["type"] == "client-1-web-camera-frame":
				self.client_1_web_camera_packet.emit(data["pil_image"])
			elif data["type"] == "client-2-web-camera-frame":
				self.client_2_web_camera_packet.emit(data["pil_image"])
			elif data["type"] == "client-3-web-camera-frame":
				self.client_3_web_camera_packet.emit(data["pil_image"])	   
			elif data["type"] == "hide_server_web_camera":
				self.hide_server_web_camera.emit()

class WebRtcServer(Process):
	def __init__(self, to_emitter, call_1_queue,call_2_queue,call_3_queue):
		super().__init__()
		if getattr(sys, 'frozen', False):
			self.ROOT = os.path.dirname(sys.executable)
		elif __file__:
			self.ROOT = os.path.dirname(__file__)
		self.pcs = [] #peer connections
		self.channels = []
		self.stream_offer = None
		self.server_webcamera_video = None
		
		self.micTracks = []
		self.blackHoles = []
		
		
		self.videoTrack = None
		
		
		
		self.video_blackHole = None
		
		self.clientWebCameraTracks = []
		self.video_blackHole_clients = []
		
		self.current_active_calls = 0
		
		self.offers_in_progress = [False,False,False]
		self.calls_answered = [False,False,False]

		self.manage_call_end_threads = []
		
		self.clients_audio_track = []
		self.clients_video_track = []
		
		self.contact_details = []
		
		self.clients_pcs = []
		
		self.webcam = None
		
		self.stop_in_progress = [False,False,False]
		
		self.to_emitter = to_emitter
		self.call_1_queue = call_1_queue
		self.call_2_queue = call_2_queue
		self.call_3_queue = call_3_queue
	
	def run(self):
		hostname = socket.gethostname()
		ip_address = socket.gethostbyname(hostname)
		self.app = web.Application()
		self.app.on_shutdown.append(self.on_shutdown)
		self.app.router.add_get("/", self.index)
		self.app.router.add_get("/video_calls.js", self.javascript)
		self.app.router.add_post("/offer", self.offer)
		self.app.router.add_post("/offer-client", self.offer_client)
		self.app.router.add_get("/signal.mp3", self.mp3)
		self.app.router.add_post("/shutdown", self.shutdown_aiohttp)
		self.app.router.add_post("/cancel_call", self.cancel_call)
		#web.run_app(self.app, access_log=None, host=str(ip_address), port=8080, ssl_context=None,keepalive_timeout=60.0,backlog=300)
		web.run_app(self.app, access_log=None, host=str(ip_address), port=80, ssl_context=None,keepalive_timeout=60.0,backlog=300)


	def get_available_cameras(self):

		devices = FilterGraph().get_input_devices()

		available_cameras = {}

		for device_index, device_name in enumerate(devices):
			available_cameras[device_index] = device_name

		return available_cameras

	def create_local_tracks(self):
		global relay
		options = {"framerate": "30", "video_size": "640x480"}
		camera_name = "video="+self.get_available_cameras()[0]
		self.webcam = MediaPlayer(camera_name, format='dshow', options=options)
		relay = MediaRelay()
		return relay.subscribe(self.webcam.video)

	async def index(self,request):
		content = open(os.path.join(self.ROOT, "index.html"), encoding="utf8").read()
		return web.Response(content_type="text/html", text=content)

	async def javascript(self,request):
		content = open(os.path.join(self.ROOT, "video_calls.js"), encoding="utf8").read()
		return web.Response(content_type="application/javascript", text=content)

	async def mp3(self,request):
		return web.FileResponse(os.path.join(self.ROOT, "signal.mp3"))
	
	async def offer_client(self,request):
		params = await request.json()
		offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

		call_number = int(params['desired_call'])
		call_number_sender = int(params["call_number"])
		
		pc = RTCPeerConnection()
		self.clients_pcs.append({"call_number_sender":call_number_sender,"call_number":call_number,"pc":pc})

		@pc.on("connectionstatechange")
		async def on_iceconnectionstatechange():
			if pc.connectionState == "closed" or pc.connectionState == "failed":
				await self.stop_client_peer_connection(pc)
		
		pc.addTrack(MediaRelay().subscribe(self.clients_audio_track[call_number-1]))
		pc.addTrack(MediaRelay().subscribe(self.clients_video_track[call_number-1]))

		# handle offer
		await pc.setRemoteDescription(offer)

		# send answer
		answer = await pc.createAnswer()
		await pc.setLocalDescription(answer)

		return web.Response(content_type="application/json",text=json.dumps({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}))


	async def offer(self,request):	
		print("Total server - client peer connections: "+str(self.current_active_calls))
		params = await request.json()
		
		
		if self.current_active_calls == 3:
			return web.Response(content_type="application/json",text=json.dumps({"sdp": "", "type": ""}))
		
		self.current_active_calls += 1
		self.stop_in_progress[self.current_active_calls-1] = False
		
		name = params["name"]
		surname = params["surname"]
		
		self.offers_in_progress[self.current_active_calls-1] = True
		self.calls_answered[self.current_active_calls-1] = False
		
		hear_call_intro_thread = threading.Thread(target=self.hear_call_intro,args=(self.current_active_calls,))
		hear_call_intro_thread.start()
		
		if self.current_active_calls == 1:
			self.to_emitter.send({"type":"call_1_offering","name":name,"surname":surname})
			data_from_mother = self.call_1_queue
		elif self.current_active_calls == 2:
			self.to_emitter.send({"type":"call_2_offering","name":name,"surname":surname})
			data_from_mother = self.call_2_queue
		else:
			self.to_emitter.send({"type":"call_3_offering","name":name,"surname":surname})
			data_from_mother = self.call_3_queue

		pc = None

		timer = 0
		while(timer<30 and data_from_mother.qsize()==0 and self.calls_answered[self.current_active_calls-1] == False):
			if request.transport is None or request.transport.is_closing():
				try:
					request.transport.close()
				except:
					pass
				pass
				break
			timer+=0.1
			await asyncio.sleep(0.1)
		self.calls_answered[self.current_active_calls-1] = True
		if data_from_mother.qsize() == 0:
			#reject offer
			while not data_from_mother.empty():
				data_from_mother.get()
			if self.current_active_calls == 1:
				self.to_emitter.send({"type":"call-1-status","status":"closed-by-server"})
			elif self.current_active_calls == 2:
				self.to_emitter.send({"type":"call-2-status","status":"closed-by-server"})
			else:
				self.to_emitter.send({"type":"call-3-status","status":"closed-by-server"})
			await self.stop_peer_connection(pc)
			if request.transport is None or request.transport.is_closing():
				return web.Response(content_type="application/json",text=json.dumps({"sdp": "", "type": ""}))
			else:
				return web.Response(content_type="application/json",text=json.dumps({"sdp": "", "type": ""}))
		else:
			data = data_from_mother.get()
			if (data["type"] == "call-1" and data["call"] == "answer") or (data["type"] == "call-2" and data["call"] == "answer") or (data["type"] == "call-3" and data["call"] == "answer"):
				while not data_from_mother.empty():
					data_from_mother.get()

				pc = RTCPeerConnection()
				pc.is_closed = False
				self.pcs.append(pc)
				self.contact_details.append({"name":name,"surname":surname})

				@pc.on("connectionstatechange")
				async def on_connectionstatechange():
					if pc.connectionState == "closed" or pc.connectionState == "failed":
						for pc_i in self.pcs:
							if id(pc_i) == id(pc):
								await self.stop_peer_connection(pc)
								break

				@pc.on("iceconnectionstatechange")
				async def on_iceconnectionstatechange():
					pass
					if pc.iceConnectionState == "failed" or pc.iceConnectionState == "closed":
						for pc_i in self.pcs:
							if id(pc_i) == id(pc):
								await self.stop_peer_connection(pc)
								break



				@pc.on("datachannel")
				async def on_datachannel(channel):
					self.channels.append(channel)
					try:
						channel.send('{"type":"local_call_number","call_number":"'+str(self.current_active_calls)+'"}')
					except:
						pass
					counter = 1
					for pc_i in self.pcs[:-1]:
						try:
							channel.send('{"type":"new-client","call_number":"'+str(counter)+'","name":"'+self.contact_details[counter-1]["name"]+'","surname":"'+self.contact_details[counter-1]["surname"]+'"}')
							counter += 1
						except:
							await self.stop_peer_connection(self.pcs[counter-1])
						

					counter = 0
					for pc_i in self.pcs[:-1]:
						try:
							self.channels[counter].send('{"type":"new-client","call_number":"'+str(self.current_active_calls)+'","name":"'+self.contact_details[counter-1]["name"]+'","surname":"'+self.contact_details[counter-1]["surname"]+'"}')
							counter += 1
						except:
							await self.stop_peer_connection(self.pcs[counter-1])
						

					@channel.on("message")
					async def on_message(message):
						if message == "disconnected":
							await self.stop_peer_connection(pc)


					async def monitor():
						while True:
							if channel.transport.transport.state == "closed":
								pass
								await self.stop_peer_connection(pc)
								break
							await asyncio.sleep(5)
					asyncio.ensure_future(monitor())


				
				#audio from server to client
				if self.stream_offer == None:
					self.stream_offer = Server_Stream_Offer()
				pc.addTrack(self.stream_offer)
				
				#video from server to client
				if self.server_webcamera_video == None:
					self.server_webcamera_video = self.create_local_tracks()
				pc.addTrack(self.server_webcamera_video)
									
				#video from server attach to QLabel
				if self.videoTrack == None:
					self.videoTrack = WebCamera(self.server_webcamera_video,self.to_emitter)
				if self.video_blackHole == None:
					self.video_blackHole = MediaBlackhole()
					self.video_blackHole.addTrack(self.videoTrack)
					await self.video_blackHole.start()
				

				
				@pc.on("track")
				async def on_track(track):	
					if track.kind == "audio":
						self.clients_audio_track.append(track)
						#audio from client (server use)
						self.micTracks.append(ClientTrack(track,self,pc,self.current_active_calls,self.to_emitter))
						self.blackHoles.append(MediaBlackhole())
						self.blackHoles[self.current_active_calls-1].addTrack(self.micTracks[self.current_active_calls-1])
						await self.blackHoles[self.current_active_calls-1].start()
					else:
						self.clients_video_track.append(track)
						#video from client (server use)
						self.clientWebCameraTracks.append(ClientWebCamera(track,self.to_emitter,self.current_active_calls,self,pc))
						self.video_blackHole_clients.append(MediaBlackhole())
						self.video_blackHole_clients[self.current_active_calls-1].addTrack(self.clientWebCameraTracks[self.current_active_calls-1])
						await self.video_blackHole_clients[self.current_active_calls-1].start()
					#for pc_i in self.pcs[:-1]:
					#	#pc_i.addTrack(MediaRelay().subscribe(track, buffered=False))
					#	pc_i.addTransceiver(track.kind)
					#	pc_i.addTrack(track)
				
				offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
				
				# handle offer
				await pc.setRemoteDescription(offer)

				# send answer
				answer = await pc.createAnswer()
				await pc.setLocalDescription(answer)

				loop = asyncio.get_event_loop()
				task = asyncio.ensure_future(self.manage_call_end(loop,self.current_active_calls))
				self.manage_call_end_threads.append(task)
				#self.manage_call_end_threads[self.current_active_calls-1].start()
				
				return web.Response(content_type="application/json",text=json.dumps({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}))
			else:
				#reject call
				while not data_from_mother.empty():
					data_from_mother.get()
				if self.current_active_calls == 1:
					self.to_emitter.send({"type":"call-1-status","status":"closed-by-server"})
				elif self.current_active_calls == 2:
					self.to_emitter.send({"type":"call-2-status","status":"closed-by-server"})
				else:
					self.to_emitter.send({"type":"call-3-status","status":"closed-by-server"})
				await self.stop_peer_connection(pc)
				return web.Response(content_type="application/json",text=json.dumps({"sdp": "", "type": ""}))

	async def stop_client_peer_connection(self,pc):		
		try:
			if pc is not None:
				try:
					await pc.close()
					counter = 0
					for pc_i in self.clients_pcs:
						if id(pc_i["pc"]) == id(pc):
							del self.clients_pcs[counter]
							break
						counter +=1
				except Exception as e:
					pass
		except Exception as e:
			pass

	async def stop_peer_connection(self,pc):
		if pc is None:
			try:
				self.offers_in_progress[self.current_active_calls-1] = False
				self.calls_answered[self.current_active_calls-1] = True
			except:
				pass
			
			self.current_active_calls -= 1
			return None
		if pc.is_closed:
			return None
		pc.is_closed = True
		call_number = 0
		counter = 0
		for pc_i in self.pcs:
			counter += 1
			if id(pc) == id(pc_i):
				call_number = counter
				break
		if call_number == 1:
			data_from_mother = self.call_1_queue
		elif call_number == 2:
			data_from_mother = self.call_2_queue
		else:
			data_from_mother = self.call_3_queue
			
		if self.stop_in_progress[call_number-1]:
			return None
		else:
			self.stop_in_progress[call_number-1] = True
		try:
			del self.contact_details[call_number-1]
			if pc is not None:
				try:
					await pc.close()
					del self.pcs[call_number-1]
				except Exception as e:
					pass
			if self.calls_answered[call_number-1] == True:
				try:
					self.channels[call_number-1].close()
					pass
				except:
					pass
			
			if self.stream_offer is not None:
				if self.current_active_calls == 1:
					self.stream_offer.stop()
					self.stream_offer.stop_offering()
					del self.stream_offer
					self.stream_offer = None
					pass
			try:
				if self.blackHoles[call_number-1] is not None:
					await self.blackHoles[call_number-1].stop()
					self.blackHoles[call_number-1] = None
					del self.blackHoles[call_number-1]
					pass
			except:
				pass
			
			try:
				if self.micTracks[call_number-1] is not None:
					self.micTracks[call_number-1].close_full()
					del self.micTracks[call_number-1]
					pass
			except:
				pass
			
			try:
				if self.current_active_calls == 1:
					try:
						self.webcam.video.stop()
						self.videoTrack.stop()
						await self.video_blackHole.stop()
						self.videoTrack = None
						self.video_blackHole = None
						pass
					except:
						pass
			except:
				pass
				
			if call_number == 1:
				self.to_emitter.send({"type":"call-1-status","status":"closed-by-client"})
			elif call_number == 2:
				self.to_emitter.send({"type":"call-2-status","status":"closed-by-client"})
			else:
				self.to_emitter.send({"type":"call-3-status","status":"closed-by-client"})


			try:
				self.clientWebCameraTracks[call_number-1].stop()
				await self.video_blackHole_clients[call_number-1].stop()
			except:
				pass
			
			try:
				del self.clientWebCameraTracks[call_number-1]
				del self.video_blackHole_clients[call_number-1]
			except:
				pass
				
			try:	
				self.calls_answered[call_number-1] = False
			except:
				pass

			try:
				del self.channels[call_number-1]
			except:
				pass

			try:
				self.offers_in_progress[call_number-1] = False
				#await self.manage_call_end_threads[call_number-1]
				del self.manage_call_end_threads[call_number-1]
			except:
				pass
			
			try:
				self.current_active_calls -=1
			except:
				pass
			try:
				if self.current_active_calls == 0:
					self.to_emitter.send({"type":"hide_server_web_camera"})
					self.server_webcamera_video = None
				
				del self.clients_audio_track[call_number-1]
				del self.clients_video_track[call_number-1]
			except:
				pass
		except Exception as e:
			pass
		
		counter = 1
		for channel in self.channels:
			try:
				channel.send('{"type":"local_call_number","call_number":"'+str(counter)+'"}')
			except:
				pass
			counter += 1
			
		for pc_i in self.clients_pcs:
			if pc_i["call_number_sender"] == call_number:
				await self.stop_client_peer_connection(pc_i["pc"])

		for pc_i in self.clients_pcs:
			if pc_i["call_number"] == call_number:
				await self.stop_client_peer_connection(pc_i["pc"])
				
		while not data_from_mother.empty():
			data_from_mother.get()
				
				
		print("END")		
		
	# to be fixed
	async def cancel_call(self,request):
		self.call_answered = True
		await self.stop_peer_connection(pc)	
		return web.Response(content_type="application/json",text=json.dumps({}))
		

	def hear_call_intro(self,call_number):
		self.audio_segment = AudioSegment.from_file(r"telephone_calls.mp3").set_frame_rate(44800)
		self.total_duration_milliseconds = len(self.audio_segment)
		self.chunk_number = 0
		self.current_duration_milliseconds = 0
		
		self.p = pyaudio.PyAudio()
		self.output_stream = self.p.open(format=pyaudio.paInt16,channels=2,rate=44800,output=True,frames_per_buffer=int(16384/4))
		self.output_stream.start_stream()
		self.packet_time = 125

		sine_segment = generators.Sine(1000).to_audio_segment()
		sine_segment = sine_segment.set_frame_rate(44800)
		sine_segment = sine_segment[(1000-int(self.packet_time))/2:self.packet_time+(1000-int(self.packet_time))/2]
		self.silent_segment = sine_segment-200


		while(self.calls_answered[call_number-1]==False):
			if((self.chunk_number+1)*(self.packet_time)<=self.total_duration_milliseconds):
				slice = self.audio_segment[self.chunk_number*(self.packet_time):(self.chunk_number+1)*(self.packet_time)]
			else:
				if((self.chunk_number)*(self.packet_time)<self.current_duration_milliseconds):
					slice = self.audio_segment[self.chunk_number*(self.packet_time):]
				else:
					slice = self.silent_segment
					self.chunk_number = 0
			self.output_stream.write(slice.raw_data)
			self.chunk_number += 1

	async def manage_call_end(self,loop,call_number):
		if call_number == 1:
			data_from_mother = self.call_1_queue
		elif call_number == 2:
			data_from_mother = self.call_2_queue
		else:
			data_from_mother = self.call_3_queue
			
		asyncio.set_event_loop(loop)
		while(self.offers_in_progress[call_number-1]):
			qsize = data_from_mother.qsize()
			if qsize == 0:
				await asyncio.sleep(1)
			else:
				data = data_from_mother.get()
				while not data_from_mother.empty():
					data_from_mother.get()
				if data["type"] == "call-1" and data["call"] == "end":
					for channel in self.channels:
						try:
							channel.send('{"type":"closing-call-1"}')
						except:
							pass
				elif data["type"] == "call-2" and data["call"] == "end":
					for channel in self.channels:
						try:
							channel.send('{"type":"closing-call-2"}')
						except:
							pass
				else:
					for channel in self.channels:
						try:
							channel.send('{"type":"closing-call-3"}')
						except:
							pass
				await self.stop_peer_connection(self.pcs[call_number-1])
				break
	
	
	async def on_shutdown(self,app):
		for pc in self.pcs:
			await self.stop_peer_connection(pc)
		raise GracefulExit()
		

	async def shutdown_aiohttp(self,request):
		await self.on_shutdown(self.app)
		return web.Response(content_type="text/html", text="")

class Server_Stream_Offer(MediaStreamTrack):
	kind = "audio"

	def __init__(self):
		super().__init__()	# don't forget this!
		
		self.q = Simple_Queue()
		
		self.codec = av.CodecContext.create('pcm_s16le', 'r')
		self.codec.sample_rate = 8000
		self.codec.channels = 2

		self.audio_samples = 0

		self.p = pyaudio.PyAudio()
		self.input_stream = self.p.open(format=pyaudio.paInt16,channels=2,rate=8000,input=True,frames_per_buffer=int(8000*0.020))
		self.input_stream.start_stream()
		
		self.run = True
		
		self.read_from_microphone_thread = threading.Thread(target=self.read_from_microphone)
		self.read_from_microphone_thread.start()
		
	async def recv(self):
		packet = av.Packet(self.q.get())
		frame = self.codec.decode(packet)[0]
		frame.pts = self.audio_samples
		frame.time_base = fractions.Fraction(1, self.codec.sample_rate)
		self.audio_samples += frame.samples
		return frame

	def read_from_microphone(self):
		while(self.run):
			in_data = self.input_stream.read(int(8000*0.020),exception_on_overflow = False)			   
			slice = AudioSegment(in_data, sample_width=2, frame_rate=8000, channels=2)
			self.q.put(slice.raw_data)

	def stop_offering(self):
		try:
			self.run = False
			self.input_stream.stop_stream()
			self.input_stream.close()
			self.read_from_microphone_thread.join()
		except Exception as e:
			pass

class WebCamera(MediaStreamTrack):
	kind = "video"

	def __init__(self,track,to_emitter):
		super().__init__()	# don't forget this!
		self.track = track
		self.to_emitter = to_emitter
		
	async def recv(self):
		frame = await self.track.recv()
		pil_image = frame.to_image()
		self.to_emitter.send({"type":"server-web-camera-frame","pil_image":[pil_image]})
		return None
		#return frame

class ClientWebCamera(MediaStreamTrack):
	kind = "video"

	def __init__(self,track,to_emitter,call_number,parent_self,pc):
		super().__init__()	# don't forget this!
		self.track = track
		self.to_emitter = to_emitter
		self.call_number = call_number
		self.parent_self = parent_self
		self.pc = pc
		#self.counter = 0
		
	async def recv(self):
		try:
			frame = await self.track.recv()
			pil_image = frame.to_image()
			if self.call_number == 1:
				self.to_emitter.send({"type":"client-1-web-camera-frame","pil_image":[pil_image]})
			elif self.call_number == 2:
				self.to_emitter.send({"type":"client-2-web-camera-frame","pil_image":[pil_image]})
			else:
				self.to_emitter.send({"type":"client-3-web-camera-frame","pil_image":[pil_image]})
			return None
		except:
			if self.call_number == 1:
				self.to_emitter.send({"type":"client-1-web-camera-frame","pil_image":[None]})
			elif self.call_number == 2:
				self.to_emitter.send({"type":"client-2-web-camera-frame","pil_image":[None]})
			else:
				self.to_emitter.send({"type":"client-3-web-camera-frame","pil_image":[None]})			 
			raise MediaStreamError

	async def stop_peer(self):
		await self.parent_self.stop_peer_connection(self.pc)				

			
class ClientTrack(MediaStreamTrack):
	kind = "audio"

	def __init__(self, track,parent_self,pc,call_number,to_emitter):
		super().__init__()
		self.track = track
		self.parent_self = parent_self
		self.pc = pc
		self.call_number = call_number
		self.to_emitter = to_emitter
		self.q = Simple_Queue()
		self.p = pyaudio.PyAudio()
		self.output_stream = self.p.open(format=pyaudio.paInt16,channels=2,rate=44800,output=True,frames_per_buffer=int(16384/4))
		self.output_stream.start_stream()
		
		self.run = True
		self.hear_client_thread = threading.Thread(target=self.hear_client)
		self.hear_client_thread.start()
		
	async def recv(self):
		# Get a new PyAV frame

		try:
			frame = await self.track.recv()
			self.q.put(frame)
		except:
			self.q.put(None)
			if self.call_number == 1:
				self.to_emitter.send({"type":"client-1-web-camera-frame","pil_image":[None]})
			elif self.call_number == 2:
				self.to_emitter.send({"type":"client-2-web-camera-frame","pil_image":[None]})
			else:
				self.to_emitter.send({"type":"client-3-web-camera-frame","pil_image":[None]})			 
			if self.run:
				self.close_full()
				raise MediaStreamError
				return None
			else:
				raise MediaStreamError
				return None
		
		
	def hear_client(self):
		while(self.run):
			frame = self.q.get()
			if frame is None:
				break
			packet_bytes = frame.to_ndarray().tobytes()
			self.output_stream.write(packet_bytes)
		
	def close_full(self):
		self.run = False
		self.hear_client_thread.join()
		self.output_stream.stop_stream()
		self.output_stream.close()

class AudioTrack(MediaStreamTrack):
	kind = "audio"

	def __init__(self, track):
		super().__init__()	# don't forget this!
		self.track = track

	async def recv(self):
		frame = await self.track.recv()			 
		return frame
		
class VideoTrack(MediaStreamTrack):
	kind = "video"

	def __init__(self, track):
		super().__init__()	# don't forget this!
		self.track = track

	async def recv(self):
		frame = await self.track.recv()			 
		return frame		


if __name__ == "__main__":
	if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
		freeze_support()
	os.system("taskkill /f /im ngrok.exe")
	hostname = socket.gethostname()
	ip_address = socket.gethostbyname(hostname)
	#tunnel = ngrok.connect(str(ip_address)+":8080", "http")
	tunnel = ngrok.connect(str(ip_address), "http","host_header:rewrite")
	program = Main(tunnel.public_url)
	
