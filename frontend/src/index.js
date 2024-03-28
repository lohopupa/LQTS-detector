canvas_container = document.getElementById("canvas-container")
canvas = document.getElementById("canvas")
label = document.getElementById("predicted-label")
ctx = canvas.getContext("2d")

window.addEventListener("resize", onResize)

function onResize(){
    canvas.width = canvas_container.clientWidth
    canvas.height = canvas_container.clientHeight
    draw()
}

const constructPath = (endpoint, args) => {
    let path = `${window.location.protocol}//${window.location.host}/api/${endpoint}`;
    // let path = `http://localhost:5000/api/${endpoint}`;
    if (args)
      path +=
        "?" +
        Object.entries(args)
          .map(([k, v]) => `${k}=${encodeURIComponent(v)}`)
          .join("&");
    return path;
  };

const [dt, updateDt] = (() => {
    let prevTime = 0;
    let time = 0;
    const dt = () => (time - prevTime) / 1000;
    const updateDt = (t) => {
        prevTime = time;
        time = t;
    };
    return [dt, updateDt];
})();

function drawLine(x1, y1, x2, y2){
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
}

function drawGrid(posX, posY, scale){
    cellSize = 5
    GridWidth = canvas.width
    GridHeight = canvas.height
    ctx.strokeStyle = "#e07b7b"
    for(let x = 0; x <= GridWidth / cellSize; x += 1){
        ctx.lineWidth = (x % 5 == 0) ? 2: 1
        drawLine(x*cellSize, 0, x*cellSize, GridHeight)
    }
    
    for(let y = 0; y <= GridHeight / cellSize; y += 1){
        ctx.lineWidth = (y % 5 == 0) ? 2: 1
        drawLine(0, y*cellSize, GridWidth, y*cellSize)
    }
}
ecg = undefined

function drawECG(){
    if(ecg == undefined) return
    ctx.strokeStyle = "#000000"
    ctx.lineWidth = 2
    // console.log(ecg)
    // drawing = false
    rowHeight = canvas.height / ecg.length
    for (let row = 0; row < ecg.length; row += 1){
        for(let x = 1; x <= ecg[row].length; x += 1){
            drawLine((x-1)*1, ecg[row][x-1]*rowHeight+rowHeight*row, x*1, ecg[row][x]*rowHeight+rowHeight*row)
        }
    }
}

let drawing = true
onResize()
function draw(time){
    updateDt(time)
    ctx.fillStyle = "#FFFFFF"
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    drawGrid(0, 0, 0)
    drawECG()
    // if(drawing) window.requestAnimationFrame(draw)
}

function normalize(min, max, v){
    return (v - min)/(max - min)
}

const handleFile = (file) => {
    file.text().then(text => {
        rows = text.trim().split("\n").map((row) => row.split(","))
        header = rows.splice(0, 1)
        ecg = new Array(12).fill().map(() => []);
        tecg = new Array(12).fill().map(() => []);
        rows.forEach((row) => {
            row.forEach((col, idx) => {
                tecg[idx].push(Number(col))
            })
        })
        tecg.forEach((col, i) => {
            let min = col[0]
            let max = col[0]
            col.forEach(v => {
                min = Math.min(min, v)
                max = Math.max(max, v)
            })
            ecg[i] = col.map(v => 1 - normalize(min, max, v))
        })
        console.log(ecg)
        draw()
    })
}


const inputElement = document.getElementById("load-file");
function onLoad() {
    const file = this.files[0]
    label.textContent = "Loading..."
    handleFile(file)
    const formData = new FormData();
    formData.append('file', file);
    fetch(constructPath("file_query"), {
        method: 'POST',
        body: formData
    }).then((response) => {
        response.json().then((r) => {
            if(r["result"]){
                label.textContent = "Predicted label: " + r["result"] 
                // console.log("RESPONSE: ", r)
            }else if(r["error"]) {
                label.textContent = "Error: " + r["error"] 
            }
        })
    }).catch(
        error => {
            label.textContent = "Something went wrong"
            console.log(error)
        }
    );
}
inputElement.addEventListener("change", onLoad, false);