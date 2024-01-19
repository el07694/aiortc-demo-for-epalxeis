// peer connection
var pc = null;
var total_clients_audio = 0;
var total_clients_video = 0;
var have_server_video = false;
var have_server_audio = false;

var local_call_number = null;
var clients_pc = [];

function createLocalPeerConnection(client_call_number,client_name,client_surname){
	var config = {
		sdpSemantics: 'unified-plan',
		iceServers: [{urls: ['stun:stun.l.google.com:19302']}]
	};
	

	clients_pc.push(new RTCPeerConnection(config));

	clients_pc[clients_pc.length-1].addEventListener('track', function(evt) {
		console.log(client_call_number);
		if (evt.track.kind == 'audio'){
			if (local_call_number == 1){
				if (client_call_number == 2){
					document.getElementById('client-audio-2').srcObject = evt.streams[0];
				}else if (client_call_number == 3){
					document.getElementById('client-audio-3').srcObject = evt.streams[0];
				}
			}else if (local_call_number == 2){
				if (client_call_number == 1){
					document.getElementById('client-audio-2').srcObject = evt.streams[0];
				}else if (client_call_number == 3){
					document.getElementById('client-audio-3').srcObject = evt.streams[0];
				}
			}else{
				if (client_call_number == 1){
					document.getElementById('client-audio-2').srcObject = evt.streams[0];
				}else if (client_call_number == 2){
					document.getElementById('client-audio-3').srcObject = evt.streams[0];
				}
			}
		}else{
			if (local_call_number == 1){
				if (client_call_number == 2){
					document.getElementById('client-video-2').srcObject = evt.streams[0];
				}else if (client_call_number == 3){
					document.getElementById('client-video-3').srcObject = evt.streams[0];
				}
			}else if (local_call_number == 2){
				if (client_call_number == 1){
					document.getElementById('client-video-2').srcObject = evt.streams[0];
				}else if (client_call_number == 3){
					document.getElementById('client-video-3').srcObject = evt.streams[0];
				}
			}else{
				if (client_call_number == 1){
					document.getElementById('client-video-2').srcObject = evt.streams[0];
				}else if (client_call_number == 2){
					document.getElementById('client-video-3').srcObject = evt.streams[0];
				}
			}
		}
	});
	


	return clients_pc[clients_pc.length-1];
}

function createPeerConnection() {
	var config = {
		sdpSemantics: 'unified-plan',
		iceServers: [{urls: ['stun:stun.l.google.com:19302']}]
	};
	

	pc = new RTCPeerConnection(config);
	//pc = new RTCPeerConnection();

	// connect audio
	pc.addEventListener('track', function(evt) {
		console.log("track");
		console.log(evt.streams[0].getTracks());
		//alert(pc.getTransceivers().length);
		if (evt.track.kind == 'audio'){
			$("#signal-audio").trigger("pause");
			$("#signal-audio").currentTime = 0; // Reset time
			document.getElementById('server-audio').srcObject = evt.streams[0];
			
			$("#control_call_button").css("visibility","hidden");
			$("#stop_call_button").css("visibility","visible");
		}else if (evt.track.kind == 'video'){
			document.getElementById('server-video').srcObject = evt.streams[0];
		}
	});
	


	return pc;
}

function negotiate() {
	return pc.createOffer({"offerToReceiveAudio":true,"offerToReceiveVideo":true}).then(function(offer) {
		return pc.setLocalDescription(offer);
	}).then(function() {
		// wait for ICE gathering to complete
		return new Promise(function(resolve) {
			console.log(pc.iceGatheringState);
			if (pc.iceGatheringState === 'complete') {
				resolve();
			} else {
				function checkState() {
					console.log(pc.iceGatheringState);
					if (pc.iceGatheringState === 'complete') {
						pc.removeEventListener('icegatheringstatechange', checkState);
						resolve();
					}
				}
				pc.addEventListener('icegatheringstatechange', checkState);

			}
		});
	}).then(function() {
		var offer = pc.localDescription;
		
		return fetch('/offer', {
			body: JSON.stringify({
				sdp: offer.sdp,
				type: offer.type,
				"name":name,
				"surname":surname
			}),
			headers: {
				'Content-Type': 'application/json'
			},
			method: 'POST'
		});
	}).then(function(response) {
		return response.json();
	}).then(function(answer) {
		if (answer.sdp == "" && answer.type == ""){
			setTimeout(call_rejected, 1000);
			return null;
		}else{
			return pc.setRemoteDescription(answer);
		}
	}).catch(function(e) {
		//alert(e);
		console.log(e);
	});
	
}

function negotiate_client(call_number) {
	return clients_pc[clients_pc.length-1].createOffer().then(function(offer) {
		return clients_pc[clients_pc.length-1].setLocalDescription(offer);
	}).then(function() {
		// wait for ICE gathering to complete
		return new Promise(function(resolve) {
			console.log(clients_pc[clients_pc.length-1].iceGatheringState);
			if (clients_pc[clients_pc.length-1].iceGatheringState === 'complete') {
				resolve();
			} else {
				function checkStateClient() {
					console.log(clients_pc[clients_pc.length-1].iceGatheringState);
					if (clients_pc[clients_pc.length-1].iceGatheringState === 'complete') {
						clients_pc[clients_pc.length-1].removeEventListener('icegatheringstatechange', checkStateClient);
						resolve();
					}
				}
				clients_pc[clients_pc.length-1].addEventListener('icegatheringstatechange', checkStateClient);

			}
		});
	}).then(function() {
		var offer = clients_pc[clients_pc.length-1].localDescription;
		
		return fetch('/offer-client', {
			body: JSON.stringify({
				sdp: offer.sdp,
				type: offer.type,
				"desired_call":call_number,
				"call_number":local_call_number
			}),
			headers: {
				'Content-Type': 'application/json'
			},
			method: 'POST'
		});
	}).then(function(response) {
		return response.json();
	}).then(function(answer) {
		return clients_pc[clients_pc.length-1].setRemoteDescription(answer);
	}).catch(function(e) {
		//alert(e);
		console.log(e);
	});
	
}



function call_rejected(){
	$("#signal-audio").trigger("pause");
	$("#signal-audio").currentTime = 0; // Reset time
	// close data channel
	if (dc) {
		dc.close();
	}

	// close local audio / video
	pc.getSenders().forEach(function(sender) {
		sender.track.stop();
	});

	// close transceivers
	if (pc.getTransceivers) {
		pc.getTransceivers().forEach(function(transceiver) {
			if (transceiver.stop) {
				transceiver.stop();
			}
		});
	}



	// close peer connection
	setTimeout(function() {
		pc.close();
		pc = null;
		console.log("Local peer connection closed");
	}, 500);

	$("#control_call_button").css("visibility","visible");
	$("#stop_call_button").css("visibility","hidden");
}

function stop_peer_connection() {
	// send disconnect message because iceconnectionstate slow to go in failed or in closed state
	dc.send("disconnected");


	$("#control_call_button").css("visibility","visible");
	$("#stop_call_button").css("visibility","hidden");
}

function start_client(client_call_number,client_name,client_surname){
	createLocalPeerConnection(client_call_number,client_name,client_surname);
	
	clients_pc[clients_pc.length-1].onclose = function() {
		// close data channel
		
		// close local audio / video
		clients_pc[clients_pc.length-1].getSenders().forEach(function(sender) {
			sender.track.stop();
		});

		// close transceivers
		if (clients_pc[clients_pc.length-1].getTransceivers) {
			clients_pc[clients_pc.length-1].getTransceivers().forEach(function(transceiver) {
				if (transceiver.stop) {
					transceiver.stop();
				}
			});
		}
		clients_pc.splice(clients_pc.length-1, 1);
		console.log("Local peer connection closed");

	};
	
	
	//negotiate_client(client_call_number);
	
	
	constraints = {audio:true,video:true};
	
	navigator.mediaDevices.getUserMedia(constraints).then(function(stream) {
		stream.getTracks().forEach(function(track) {
			clients_pc[clients_pc.length-1].addTrack(track, stream);
		});
		return negotiate_client(client_call_number);
		}, function(err) {
			alert('Could not acquire media: ' + err);
	});
	
}

function start(name,surname) {
	$("#signal-audio").trigger("play");
	pc = createPeerConnection();
	
	dc = pc.createDataChannel('chat', {"ordered": true});
	dc.onclose = function() {
		
	};
	dc.onopen = function() {
		
	};
	dc.onmessage = function(evt) {
		console.log(evt.data);
		data = JSON.parse(evt.data);
		if(data["type"] == "closing"){
			stop_peer_connection();
		}
		
		if (data["type"] == "local_call_number"){
			local_call_number = data["call_number"];
		}
		
		if (data["type"] == "new-client"){
			var client_call_number = data["call_number"]
			var client_name = data["name"]
			var client_surname = data["surname"]
			start_client(client_call_number,client_name,client_surname)
			
		}
		
	};
	
	pc.onclose = function() {
		// close data channel
		if (dc) {
			dc.close();
		}

		// close local audio / video
		pc.getSenders().forEach(function(sender) {
			sender.track.stop();
		});

		// close transceivers
		if (pc.getTransceivers) {
			pc.getTransceivers().forEach(function(transceiver) {
				if (transceiver.stop) {
					transceiver.stop();
				}
			});
		}
		pc = null;
		console.log("Local peer connection closed");

	
	};
	
	
	
	//negotiate();
	
	constraints = {audio:true,video:true};
	
	navigator.mediaDevices.getUserMedia(constraints).then(function(stream) {
		stream.getTracks().forEach(function(track) {
			pc.addTrack(track, stream);
			if (track.kind == "video"){
				//correct
				document.getElementById('client-video-1').srcObject = stream;
			}
		});
		return negotiate();
		}, function(err) {
			alert('Could not acquire media: ' + err);
	});
	
	
}

$(document).ready(function(){
	$("#control_call_button").on( "click", function() {
		name = $("#name").val();
		surname = $("#surname").val();
		start(name,surname)
	});
	
	$("#stop_call_button").on( "click", function() {
		stop_peer_connection();
	});
})

/*
window.addEventListener("beforeunload", function (e) {
	console.log("Before unload");
	fetch('/cancel_call', {
			body: JSON.stringify({}),
			headers: {
				'Content-Type': 'application/json'
			},
			method: 'POST'
		});
	const sleep = ms => new Promise(r => setTimeout(r, 5000));
});
*/