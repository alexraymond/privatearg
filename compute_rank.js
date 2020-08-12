/////////////////////////////////////////
/////////// UTILITY FUNCTIONS ///////////
/////////////////////////////////////////


function arraysEqual(_arr1, _arr2){
	// funzione che controlla se due array hanno gli stessi elementi
    if (!Array.isArray(_arr1) || ! Array.isArray(_arr2) || _arr1.length !== _arr2.length) return false;
    var arr1 = _arr1.concat().sort();
    var arr2 = _arr2.concat().sort();
    for (var i = 0; i < arr1.length; i++) {
        if (arr1[i] !== arr2[i]) return false;
    }
    return true;
}


function isIntoSet(_arr1, _set){
	// funzione che controlla se un dato array Ã¨ contenuto in un set di array
	control = false;
	_arr1.sort();
 	$.each(_set, function(index, inserted){
 		inserted.sort();
        is_same = (inserted.length == _arr1.length) && inserted.every(function(element, index) {
            return element === _arr1[index];
        });
        if(is_same) control = true; //console.log(inserted,out_args,is_same, control);
    });
    return control; // Risponde ture se l'array Ã¨ nel set, false altrimenti
}

function payoff(_arr1, _set){
	// funzione che controlla se un dato array Ã¨ contenuto in un set di array
	control = 0;
	_arr1.sort();
 	$.each(_set, function(index, inserted){
 		inserted.sort();
        is_same = (inserted.length == _arr1.length) && inserted.every(function(element, index) {
            return element === _arr1[index];
        });
        if(is_same) control = 1; //console.log(inserted,out_args,is_same, control);
    });
    return control; // Risponde 1 se l'array Ã¨ nel set, 0 altrimenti
}

function factorial(integer) {
	var Resfact = 1;
	for (var K=1; K < integer+1; K++) {
		Resfact = Resfact * K;
	}
	return Resfact;
}


function getExtS(_i){
	// restituisce il set delle estensioni "S" creando l'insieme delle parti dagli argomenti, sottraendo l'argomento i
	var ta = getArguments();
	var temp = [];

	$.each(ta, function(id, el){
		if (el != _i) temp.push(el);
	});

	const getAllSubsets =
	theArray => theArray.reduce(
		(subsets, value) => subsets.concat(
			subsets.map(set => [value,...set])
		),
		[[]]
	);
	extS = getAllSubsets(temp)
	return extS // [["2"], ["1", "5"], ["3", "2"]]
}

function numberOfSwinger(_subset, _set){
	// _set = [["2"], ["1", "5"], ["3", "2"]]
	var quanti = 0;
	var arrayofswing = []
	$.each(_subset, function(ind, el){
			var temp = [];
			$.each(_subset, function(a, b){
				if (b != el) temp.push(b);
			});
			if (!isIntoSet(temp, _set)) {
				if (!arrayofswing.includes(el)){
					quanti++;
					arrayofswing.push(el);
					//console.log(arrayofswing)
				}
			}
	});
	return quanti;
}

function getNumberOfWinners(_ext){
	// restituisce il numero di estensioni in cui compare i
	var num = 0;
	$.each(_ext, function(id, el){
			num++;
	});
	return num // numero di estensioni in cui compare "i"
}

function minimalWinnings(_ext) {
    //returns the set of minimal winning coalitions
    //_ext=[["2"], ["1", "5"], ["3", "2"]]

    var mW = [];
    var isEmptyExt = false;

    //if [] is an extension, it is always the minimal
    $.each(_ext, function(id, el) {
        if(el.length == 0) {
            mW.push(el);
            isEmptyExt = true;
            return false;
        }
    });

    if(isEmptyExt) return mW;

    $.each(_ext, function(id1, el1) {
        is_el1_min = true;
        $.each(_ext, function(id2, el2) {
            if(el1.length > el2.length) {
                //console.log("checking",el1,el2);
                el2.every(function(item) {
                    if(el1.indexOf(item) !== -1) {
                        is_el1_min = false;
                        //console.log(el1,"contains",el2);
                    }
                });
            }
        });
        if(is_el1_min) {
            mW.push(el1);
            //console.log(el1,"is minimal");
        }
    });

    //console.log(mW);
    return mW;

}

//////////////////////////////////////////
///////////// CORE FUNCTIONS /////////////
//////////////////////////////////////////


function getFramework() {
	// get array of arguments
	var framework = []; //return array
	var attText = $('#testo').val(); // get text of the framework
	framework = attText.split(")."); // format retireved string into array
	return framework; // ["2", "1", "5", "3"]
}


function getArguments() {
	// get array of arguments
	var arrayArg = []; //return array
	var arrayFW = getFramework() // format retireved string into array
	$.each(arrayFW, function( index, element ) { // for eachtextline
		if (element.indexOf("arg(") >= 0){
		    arrayArg.push(element.split('arg(')[1]);
		}
	});
	return arrayArg; // ["2", "1", "5", "3"]
}


function getAttacks() {
	// get array of attacks
	var arrayAtt = [];
	var arrayFW = getFramework() // format retireved string into array
	$.each(arrayFW, function( index, element ) { // for eachtextline
        if (element.indexOf("att(") >= 0){
            arrayAtt.push(element.split('att(')[1]);
        }
    });
	return arrayAtt; // ["2,3", "1,2", "5,4", "3,1"]
}


function getExtIN(){
	//esegue la lettura da conarg e restituisce le estensioni
	var extIN = []; // return array
    //$('#solArea').val('');
	//saveF(); //calling conarg solution function
	var text = $('#solArea').val(); //console.log("text: "+ text); // retrieving the text solution
	// formatting the string returned from conarg text pad into array
	var righe = text.replace(/\r\n/g, "\n").replace(/\n/g, "\r\n").split("\r\n");
    righe.splice(-1,1); //console.log("righe: ", righe);
	$.each(righe, function( index, element ) { // for esch element of the array
        var k = null;
        var arrtemp = [];
		k = element.replace("{", "").replace("}", ""); //console.log("k", k); // clean the element of the array
        arrtemp = k.split(" "); //console.log("temp: ", arrtemp);
        if (arrtemp[0] == "") arrtemp = [];
        extIN.push(arrtemp);  //console.log("each extIN: ", extIN); // push the elements into return array
    });
	//console.log(righe);
	//$('#solArea').val(''); // cleaning the text area
	//console.log(extIN); alert(extIN);
	return extIN // [["2"], ["1", "5"], ["3", "2"]]
}


function getExtOUT(extIN, attacks){
    //input: insieme di estensioni IN e attacchi
	//output: insieme di estensioni OUT

    var extOUT = [];
    $.each(extIN, function(index1, extension){ //console.log("extension", index1, extension);
        var out_args = [];
        if(extension.length != 0) { //trovo gli argomenti in ogni estensione
        $.each(extension, function(index2, argument){ //console.log("argument", index2, argument);
            $.each(attacks, function(index3, attack){ //console.log("attack", index, attack);
                var attacker = attack.split(",")[0]; //trovo l'attaccante in ogni attacco
                var attacked = attack.split(",")[1];//trovo l'attaccato in ogni attacco
                if(argument == attacker) { //console.log("attack", attacker, "->", attacked);
                    if($.inArray(attacked, out_args) == -1) { //aggiungo solo se non Ã¨ giÃ  presente
                        out_args.push(attacked);
                    }
                }
            }); //END for each attack
        }); //END for each argument
        }
        //console.log(out_args);
        if(!isIntoSet(out_args,extOUT)) { //aggiungo solo se non Ã¨ giÃ  presente
            extOUT.push(out_args);
        }
    }); //END for each extension

    //console.log(extOUT);
	return extOUT; //esempio: [[""], ["1"], ["2", "3"]]

    /*
    //ese1
    ext = [[""], ["3"], ["2"], ["2,3"], ["1"]];
    att = ["1,2", "2,1", "1,3"];
    getExtOUT(ext,att);

    //ese2
    ext = [["3"], ["2"], ["2,1"], ["1"]];
    att = ["1,3", "2,3"];
    getExtOUT(ext,att);

    //ese3
    ext = [["3"], ["2"], ["2,1"], ["1"], ["1,2,4,6"]];
    att = ["1,3", "2,3", "1,5", "2,5", "2,7"];
    getExtOUT(ext,att);
    */
}


function computeSV(i, n, extensions) {
	//console.log(i); console.log(n); console.log(extensions);
	// la funzione prende in input l'argomento _i, il numero degli argomenti, e il set delle estensioni
	// restituisce il valore SV calcolato, su _i

	var SV = 0;
	var gain = 0;
	var cardinalityOfS;
	var S_n = getExtS(i);
	var Si = [];
	const semantic = extensions;

	$.each(S_n, function(ind, S){
		cardinalityOfS = S.length;
		Si = [];
		var temp = [];
		$.each(S, function(id, el){
			temp.push(el);
		});
		temp.push(i);
		Si = temp;
		gain = payoff(Si, semantic) - payoff(S, semantic);
		SV += (gain * factorial(cardinalityOfS) *  factorial(n - cardinalityOfS - 1)) / factorial(n);
	});
	//console.log("Per orgni i =", i, "\n S", S, "Si", Si)
	return SV;
}

function computeBI(i, n, extensions) {
	// la funzione prende in input l'argomento _i, il numero degli argomenti, e il set delle estensioni
	// restituisce il valore BI calcolato, su _i
	var BI = 0;
	var gain = 0;
	var cardinalityOfS;
	var S_n = getExtS(i);
	var Si = [];
	const semantic = extensions;

	$.each(S_n, function(ind, S){
		Si = [];
		var temp = [];
		$.each(S, function(id, el){
			temp.push(el);
		});
		temp.push(i);
		Si = temp;
		gain = payoff(Si, semantic) - payoff(S, semantic);
		BI += gain/Math.pow(2, n-1);

	});
	return BI;
}

function computeJI(i, n, extensions) {
	// la funzione prende in input l'argomento _i, il numero degli argomenti, e il set delle estensioni
	// restituisce il valore BI calcolato, su _i
	var JSi = 0;
	var gain = 0;
	var cardinalityOfS;
	var S_n = getExtS(i);
	var Si = [];
	const semantic = extensions;

	$.each(S_n, function(ind, S){
		Si = [];
		var temp = [];
		$.each(S, function(id, el){
			temp.push(el);
		});
		temp.push(i);
		Si = temp;
		gain = payoff(Si, semantic) - payoff(S, semantic);
		var NumbSwing = numberOfSwinger(Si, extensions);
		if ( NumbSwing != 0 ) {
			JSi += gain/NumbSwing;
		}

	});
	return JSi;
}

function computeDP(i, ext, coal) {
	//input: player i, set winning coalitions, set of minimal winning coalitions
	//output DP value for player i

	var DP = 0;

    //cartinality of the minimal winning coalitions' set
    var cardOfMv = coal.length;

    //minimal winning coalitions containing i
    var Mv_i = [];
    $.each(coal, function(id, el){
        if(el.includes(i)) {
            //eliminate i from el
            var el2 = el.filter(function(value, index, arr){
                return value != i;
            });
            Mv_i.push(el2); //console.log(el,"is in Mv_i for",i);
        }
    }); //console.log("Mv_i",Mv_i);

    //computing DP
    var sum = 0;

    $.each(Mv_i,function(id,S){
        if(S.length > 0) {
            //add i to S
            var S_i = [];
            $.each(S, function(id2, el2){
                S_i.push(el2);
            });
            S_i.push(i);

            //console.log("i: "+i,"S_i: "+S_i,"S: "+S);
            var gain = payoff(S_i, ext) - payoff(S, ext);

            sum += gain/S.length;

        }
    });

    DP = sum/coal.length
	return DP;

}


function computePI(arguments, attacks, extIN, extOUT, powerindex){ //console.log(arguments, powerindex);
	var arrayPI = []; //array di [arg][indexIN][indexOUT]
	//per ogni argumento calcolo il powerindex

	var n = arguments.length; //console.log(extIN);

	$.each(arguments, function(index, element){
		var a = element;
		var b;
		var c;
		switch (powerindex) {
			case 'SV':
				// ESEGUO SHAPLEY
                //console.log(extIN);
				b = computeSV(a, n, extIN).toFixed(5); //console.log("b:", b);
				c = computeSV(a, n, extOUT).toFixed(5);
				break;
			case 'BI':
				// ESEGUO BANZHAF
                b = computeBI(a, n, extIN).toFixed(5); //console.log("b:", b);
				c = computeBI(a, n, extOUT).toFixed(5);
				break;
			case 'JI':
				// ESEGUO JOHNSTONE
                b = computeJI(a, n, extIN).toFixed(5); //console.log("b:", b);
				c = computeJI(a, n, extOUT).toFixed(5);
				break;
			case 'DP':
				// ESEGUO DEEGAN-PAKEL
                var minIN = minimalWinnings(extIN); //console.log("minIN", minIN);
                var minOUT = getExtOUT(minIN, attacks); //console.log("minOUT", minOUT);
                //insert emptyset
                if(!isIntoSet([], minIN)) minIN.push([]);
                if(!isIntoSet([], minOUT)) minOUT.push([]);
                b = computeDP(a, extIN, minIN).toFixed(5); //console.log("b:", b);
				c = computeDP(a, extOUT, minOUT).toFixed(5);
				break;
		}
		arrayPI.push([a, b, c]); // inserisco ogni computazione nell'array
	});
	return arrayPI;
}



function sortByPI(arrayPI){
	/*
    * Orders the array of PI as follows:
    * if indexINa > indexINb -> a > b, else
    * if indexINa < indexINb -> b > a, else
    * if indexOUTa < indexOUTb -> a > b, else
    * if indexOUTa > indexOUTb -> b > a, else
    * lexicographic order
    */
    arrayPI.sort(function(a, b){ //console.log(a,b);
        return ((Number(a[1]) > Number(b[1])) ? -1 : (Number(a[1]) < Number(b[1])) ? 1 : (Number(a[2]) < Number(b[2])) ? -1 : (Number(a[2]) > Number(b[2])) ? 1 : (a[0] < b[0]) ? -1 : 0);
    });
	return arrayPI;

    /*
    //ex1
    arrayPI = [["a",3,8],["b",6,1],["c",2,2],["d",3,2],["e",7,4]];
    */
}


function orderdPrint(ordered_array){
	//stampa la soluzione ordinata secondo l'ultimo
    //console.log(ordered_array);
    var barraS = document.getElementById("barraSoluzioni");
	barraS.classList.remove("visBarS");

    var ranking_text = "";
    var string = "";
    var l = ordered_array.length;
    for(i=0; i<l-1; i++) {
        symbol = (Number(ordered_array[i][1]) > Number(ordered_array[i+1][1]) || Number(ordered_array[i][2]) < Number(ordered_array[i+1][2])) ? "\u227B" : "\u2243";
        ranking_text += ordered_array[i][0]+" "+symbol+" ";
    }
    ranking_text += ordered_array[l-1][0]+"\n";

    //set alphanumeric order
    ordered_array.sort(function(a, b){
        return a[0].localeCompare(b[0]);
    });

    $.each(ordered_array, function(index,argument){
        string += "arg: "+argument[0]+"\n";
        string += "IN: "+argument[1]+"\n";
        string += "OUT: "+argument[2]+"\n\n";
    });

    $("#solArea").html(ranking_text+"\n"+string);
    $("#solArea").text(ranking_text+"\n"+string);
    $("#solArea").val(ranking_text+"\n"+string);
	return;

}




////////////////////////////////////////
//////////////// COLORS ////////////////
////////////////////////////////////////


function colorThings(name, color, overzero) {

	svgPlane = document.getElementsByTagName("svg")[0];
	nodes = svgPlane.childNodes[5]; //array con tutte le g dei nodi
	len1 = nodes.childNodes.length; //numero di g ("nodi")
	//per tutti i nodi del grafo
	for(var i=0; i<len1; i++) {

		gNode = nodes.childNodes[i]; //g
		circle = gNode.childNodes[1]; //text

		text = circle.textContent; // testo = nodo
		if (name == text ){
			gNode.childNodes[0].setAttribute( 'fill', color );// coloro il nodo con il nome uguale alla lista
			if (overzero) {
				gNode.childNodes[0].setAttribute("style", "stroke: green");
			} else {
				gNode.childNodes[0].setAttribute("style", "stroke: red");
			}
		}

	}
	return;
}


function colorRange(_color1, _color2, n) {
	//presi due estremi di colore espressi in esadecimanle, ed una n, calcola n livelli intermedi
	// restituisce un array di colori
	var result = [];
	for(var i = 0; i<3; i++) {
		var sub1 = _color1.substring(1+2*i, 3+2*i);
		var sub2 = _color2.substring(1+2*i, 3+2*i);
		var v1 = parseInt(sub1, 16);
		var v2 = parseInt(sub2, 16);
		var gap = Math.floor((v1 - v2) / n);
		var temp = v1;
		for (var k = 0; k < n-1; k++) {
			if (i == 0 ) result[k] = "#";
			var sub = temp.toString(16).toUpperCase();
			var padsub = ('0'+sub).slice(-2);
			result[k] += padsub;
			temp = temp - gap;
		}

	}
	result[n-1] = _color2.toUpperCase();;
	return result;
}


function colorPrint(ordered_array){
	//stampa la soluzione ordinata secondo l'ultimo
    //colori per la stampa
    var colorCap = '#eeeeee';
    var colorBottom = '#444444';
    var arrOfColors = [];

    var l = ordered_array.length;
    var preferedCount = 0;

    for(var i=0; i<l-1; i++) {
        if (ordered_array[i][1] > ordered_array[i+1][1] || ordered_array[i][2] < ordered_array[i+1][2]) {
        	preferedCount++; // a is prefered then b
        }
    }

	arrOfColors = colorRange ( colorCap, colorBottom, preferedCount+1);

    l = ordered_array.length;
    var indexPreference = 0;
    for(var i=0; i<l; i++) {
        var overzero = (ordered_array[i][1] >= 0) ;
        colorThings(ordered_array[i][0], arrOfColors[indexPreference], overzero);
        if (i <l-1)
        if ( (ordered_array[i][1] > ordered_array[i+1][1] || ordered_array[i][2] < ordered_array[i+1][2]) ) {
        	indexPreference++;
        }
    }
	return;
}




/////////////////////////////////////////
//////////// START EXECUTION ////////////
/////////////////////////////////////////

function saveG_(){
	var arguments = getArguments(); //retrieve the arguments
	var attacks = getAttacks();  //retrieve the attacks
	var powerindex = $('#selRank').val(); //get power index selector
	var extIN = getExtIN(); //console.log("extIN", extIN);
	var extOUT = getExtOUT(extIN, attacks); //console.log("extOUT", extOUT);
	var arrayPI = computePI(arguments, attacks, extIN, extOUT, powerindex); //console.log("arrayPI", arrayPI);
	var ordered_array = sortByPI(arrayPI); //console.log("ordered_array", ordered_array);
	orderdPrint(ordered_array);
    colorPrint(ordered_array);
}

