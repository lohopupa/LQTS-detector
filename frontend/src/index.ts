const canvasContainer = document.getElementById("canvas-container") as HTMLElement;
const canvas = document.getElementById("canvas") as HTMLCanvasElement;
const label = document.getElementById("predicted-label") as HTMLElement;
const ctx = canvas.getContext("2d") as CanvasRenderingContext2D;
const qtLabel = document.getElementById("qt") as HTMLElement;
const rrLabel = document.getElementById("rr") as HTMLElement;
const qtcLabel = document.getElementById("qtc") as HTMLElement;


window.addEventListener("resize", onResize);

function onResize() {
    canvas.width = canvasContainer.clientWidth;
    canvas.height = canvasContainer.clientHeight;
    draw();
}

function drawLine(x1: number, y1: number, x2: number, y2: number) {
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
}

function setLabels(res: string, qt?: string, rr?: string, qtc?: string){
    label.textContent = res;
    qtLabel.textContent = "QT: " + (qt ?? "")
    rrLabel.textContent = "RR: " + (rr ?? "")
    qtcLabel.textContent = "QTc: " + (qtc ?? "")
}

function drawGrid() {
    const cellSize = 10;
    const gridWidth = canvas.width;
    const gridHeight = canvas.height;
    ctx.strokeStyle = "#e07b7b";

    for (let x = 0; x <= gridWidth / cellSize; x += 1) {
        ctx.lineWidth = (x % 5 == 0) ? 2 : 1;
        drawLine(x * cellSize, 0, x * cellSize, gridHeight);
    }

    for (let y = 0; y <= gridHeight / cellSize; y += 1) {
        ctx.lineWidth = (y % 5 == 0) ? 2 : 1;
        drawLine(0, y * cellSize, gridWidth, y * cellSize);
    }
}

let ecg: number[][] | undefined = undefined;

let rs: number[] = []
let qs: number[] = []
let ts: number[] = []

function drawPeaks(){
    ctx.lineWidth = 2
    ctx.strokeStyle = "magenta"
    for(const r of rs){
        drawLine(r, 0, r, canvas.height)
    }
    ctx.strokeStyle = "blue"
    for(const q of qs){
        drawLine(q, 0, q, canvas.height)
    }
    ctx.strokeStyle = "green"
    for(const t of ts){
        drawLine(t, 0, t, canvas.height)
    }
}

function drawECG() {
    if (ecg === undefined) return;
    ctx.strokeStyle = "#000000";
    ctx.lineWidth = 2;

    const rowHeight = canvas.height / ecg.length;
    for (let row = 0; row < ecg.length; row += 1) {
        for (let x = 1; x < ecg[row].length; x += 1) {
            drawLine(
                (x - 1) * 1,
                ecg[row][x - 1] * rowHeight + rowHeight * row,
                x * 1,
                ecg[row][x] * rowHeight + rowHeight * row
            );
        }
    }
}

let drawing = true;
onResize();

function draw() {
    ctx.fillStyle = "#FFFFFF";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    drawGrid();
    drawECG();
    drawPeaks();
}

function normalize(min: number, max: number, v: number): number {
    return (v - min) / (max - min);
}

const handleFile = (file: File) => {
    file.text().then(text => {
        const rows = text.trim().split("\n").map(row => row.split(",").map(Number));
        rows.shift(); // remove header

        ecg = new Array(12).fill(0).map(() => []);
        const tempECG: number[][] = new Array(12).fill(0).map(() => []);

        rows.forEach(row => {
            row.forEach((col, idx) => {
                tempECG[idx].push(col);
            });
        });

        tempECG.forEach((col, i) => {
            const min = Math.min(...col);
            const max = Math.max(...col);
            ecg![i] = col.map(v => 1 - normalize(min, max, v));
        });

        draw();
    });
};

const inputElement = document.getElementById("load-file") as HTMLInputElement;

type Result = {
    result?: string
    error?: string
    qs: number[]
    ts: number[]
    rs: number[]
    qt: string
    rr: string
    qtc: string
}

async function imageOnLoad() {
    const file = inputElement.files?.[0];
    if (!file) return;

    setLabels("Обработка...")
    handleFile(file);

    const formData = new FormData();
    formData.append("file", file);

    const resp = await fetch(
        "api/file_query",
        {
            method: "POST",
            body: formData
        }).catch(error => {
            setLabels("Что-то пошло не так!")
            console.log(error);
        }) as Response;
    const res = await resp.json() as Result

    if (res.result) {
        setLabels("Результат: " + res.result, res.qt, res.rr, res.qtc)
        rs = res.rs
        qs = res.qs
        ts = res.ts
    } else if (res.error) {
        setLabels("Ошибка: " + res.error)
        rs = []; 
        qs = []; 
        ts = []; 
    }
    draw()
}

inputElement.addEventListener("change", imageOnLoad, false);
