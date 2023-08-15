/**
 * @param {int} type : 0(connect), 1(request), 2(add), 3(delete), 4(bed pos), 5(diag pos), 6(confirm), 7(add daily), 8(edit daily) 중 하나
 * @param {string} header : "t"(eacher), "s"(tudent)
 * @param {*} body : content body, 내용이 들어가야 함(배열 형식)
 * @returns : json string
 */
export const form = ({type=1, stat=1, header="", body=[]}) => {
    return JSON.stringify({
        "type": type,
        "stat": stat,
        "content": {
            "header": header,
            "body": body
        }
    });
};

export const copy = (data) => {
    return JSON.parse(JSON.stringify(data));
};

export const errorHandling = ({message="통신 간 오류가 발생하였습니다. 재접속합니다.", reload=false, locate="./"}) => {
    const alarm = document.getElementById("alerting");
    alarm.querySelector("#mention").innerText = message;
    alarm.removeAttribute("hidden");
    setTimeout(() => {
        alarm.setAttribute("hidden", true);
        if(reload){
            //location.href = locate;
        }
    }, 3000);
};

export const loading = (flag=false) => {
    const spinner = document.getElementById("spinner");
    if(flag){
        spinner.setAttribute("hidden", true);
        document.querySelector("body").style.pointerEvents = "auto";
    } else {
        spinner.removeAttribute("hidden");
        document.querySelector("body").style.pointerEvents = "none";
    }
};