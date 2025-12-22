#include <iostream>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <vector>
#include <string>
#include <cmath>
#include <filesystem>
#include <array>
#include <map>
#include <type_traits>
#include <cctype>

struct Params {
    // 0:地层密度(g/cm3) 1:Eaton指数 2:横波a 3:横波b
    // 4:泊松比1         5:泊松比2  6:弹模1  7:弹模2
    // 8:最小构造        9:最大构造 10:Biot
    double v[11] = { 1.4, 0.45, 0.741, -0.694, 0.5, 0.2, 1.0, 0.0, 0.28, 0.5, 1.0 };
    double& operator[](size_t i) { return v[i]; }
    const double& operator[](size_t i) const { return v[i]; }
};

using Row = std::array<double, 5>; // 0:深度 1:曲线Y 2:? 3:密度 4:?
using Matrix = std::vector<Row>;

static constexpr double G = 0.00981;    // 与原式一致
static constexpr double ONE_MILLION = 1e6;
static constexpr double rho_hydro=1.07; //（正常静水压力当量密度，单位 g/cm3）
void help(const char* pname) {
    std::cout << "Usage: " << pname << " -i input.las -w workdir [options]\n";
    std::cout << "Required:\n";
    std::cout << "  -i, --input         输入数据文件（至少含5列，缺失值<=--nodata）\n";
    std::cout << "  -w, --workdir       输出目录（不存在则创建）\n";
    std::cout << "Coefficients (可选，默认见括号)：\n";
    std::cout << "  --dens    地层密度(g/cm3)            (1.4)\n";
    std::cout << "  --eaton   Eaton指数                   (0.45)\n";
    std::cout << "  --a       横波系数a                   (0.741)\n";
    std::cout << "  --b       横波系数b                   (-0.694)\n";
    std::cout << "  --nu1     泊松比系数1                 (0.5)\n";
    std::cout << "  --nu2     泊松比系数2                 (0.2)\n";
    std::cout << "  --e1      弹性模量系数1               (1)\n";
    std::cout << "  --e2      弹性模量系数2               (0)\n";
    std::cout << "  --kmin    最小水平主应力构造系数      (0.28)\n";
    std::cout << "  --kmax    最大水平主应力构造系数      (0.5)\n";
    std::cout << "  --biot    Biot系数                    (1)\n";
    std::cout << "Other options:\n";
    std::cout << "  --prec    输出小数位（默认6）\n";
    std::cout << "  --nodata  缺失阈值，<=该值视为无效     (默认-999)\n";
    std::cout << "  -h, --help   显示此帮助\n";
    std::cout << "\nExample:\n";
    std::cout << "  " << pname << " -i data.las -w ./out --dens 1.45 --eaton 0.5 --biot 0.9 --prec 6\n";
}

std::map<std::string, std::string> parseCommandLine(int argc, char* argv[]) {
    std::map<std::string, std::string> opts;
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "-h" || arg == "--help") {
            opts["help"] = "1";
            break;
        }
        if (arg.rfind("--", 0) == 0) {
            std::string key = arg.substr(2);
            if (i + 1 >= argc) {
                std::cerr << "Missing value for option: " << arg << "\n";
                opts["__error__"] = "1";
                break;
            }
            std::string val = argv[++i];
            opts[key] = val;
        } else if (arg == "-i") {
            if (i + 1 >= argc) { std::cerr << "Missing value after -i\n"; opts["__error__"]="1"; break; }
            opts["input"] = argv[++i];
        } else if (arg == "-w") {
            if (i + 1 >= argc) { std::cerr << "Missing value after -w\n"; opts["__error__"]="1"; break; }
            opts["workdir"] = argv[++i];
        } else {
            std::cerr << "Unknown argument: " << arg << "\n";
            opts["__error__"] = "1";
            break;
        }
    }
    return opts;
}

bool checkCommands(const std::map<std::string, std::string>& opts) {
    if (opts.count("input") < 1) return false;
    if (opts.count("workdir") < 1) return false;
    return true;
}

template <class T>
T parseValue(const std::map<std::string, std::string>& opts, const std::string& key, T default_value) {
    if (opts.count(key) < 1) return default_value;
    const std::string& val = opts.at(key);

    if constexpr (std::is_same<T, int>::value) {
        try { return std::stoi(val); } catch (...) { return default_value; }
    } else if constexpr (std::is_same<T, float>::value) {
        try { return std::stof(val); } catch (...) { return default_value; }
    } else if constexpr (std::is_same<T, double>::value) {
        try { return std::stod(val); } catch (...) { return default_value; }
    } else if constexpr (std::is_same<T, bool>::value) {
        std::string s = val; for (auto& c : s) c = std::tolower(c);
        if (s=="1"||s=="true"||s=="yes"||s=="on") return true;
        if (s=="0"||s=="false"||s=="no"||s=="off") return false;
        try { return bool(std::stoi(val)); } catch (...) { return default_value; }
    } else if constexpr (std::is_same<T, std::string>::value) {
        return val;
    } else {
        static_assert(
            std::is_same<T,int>::value || std::is_same<T,float>::value ||
            std::is_same<T,double>::value || std::is_same<T,bool>::value ||
            std::is_same<T,std::string>::value, "Unsupported type for parseValue");
    }
    return default_value;
}

// 读取文本数据，忽略#注释，每行读前5列，不足补-1e12
bool readLasData(const std::string& path, Matrix& las) {
    std::ifstream in(path);
    printf("Reading input file: %s\n", path.c_str());
    if (!in)
    {
        printf("Cannot open input file: %s\n", path.c_str());
        return false;
    }
    std::string line;
    while (std::getline(in, line)) {
        auto hash = line.find('#');
        // printf  ("line: %s\n", line.c_str());
        if (hash != std::string::npos) line = line.substr(0, hash);
        // printf  ("trim: %s\n", line.c_str());
        std::istringstream iss(line);
        std::vector<double> vals;
        double x;
        while (iss >> x) vals.push_back(x);
        if (vals.empty()) continue;
        Row r{};
        for (int i = 0; i < 5; ++i) r[i] = (i < (int)vals.size() ? vals[i] : -1e12);
        las.push_back(r);
    }
    printf("Read %zu rows from %s\n", las.size(), path.c_str());

    return true;
}

int main(int argc, char* argv[]) {
#ifdef _WIN32
    system("chcp 65001 > nul"); // 控制台UTF-8（Windows可选）
#endif
    if (argc < 2) { help(argv[0]); return 1; }

    auto opts = parseCommandLine(argc, argv);
    if (opts.count("help")) { help(argv[0]); return 0; }
    if (opts.count("__error__")) { return 2; }
    if (!checkCommands(opts)) { help(argv[0]); return 3; }

    // 基本参数
    std::string filepath = parseValue<std::string>(opts, "input", "");
    std::string workpath = parseValue<std::string>(opts, "workdir", ".");
    int prec = parseValue<int>(opts, "prec", 6);
    double nodata = parseValue<double>(opts, "nodata", -999.0);

    // 系数
    Params sn; // 默认值
    sn[0]  = parseValue<double>(opts, "dens",  sn[0]);
    sn[1]  = parseValue<double>(opts, "eaton", sn[1]);
    sn[2]  = parseValue<double>(opts, "a",     sn[2]);
    sn[3]  = parseValue<double>(opts, "b",     sn[3]);
    sn[4]  = parseValue<double>(opts, "nu1",   sn[4]);
    sn[5]  = parseValue<double>(opts, "nu2",   sn[5]);
    sn[6]  = parseValue<double>(opts, "e1",    sn[6]);
    sn[7]  = parseValue<double>(opts, "e2",    sn[7]);
    sn[8]  = parseValue<double>(opts, "kmin",  sn[8]);
    sn[9]  = parseValue<double>(opts, "kmax",  sn[9]);
    sn[10] = parseValue<double>(opts, "biot",  sn[10]);
    printf("参数: 地层密度=%.3f g/cm3, Eaton指数=%.3f, 横波a=%.3f, 横波b=%.3f\n", sn[0], sn[1], sn[2], sn[3]);
    printf("      泊松比1=%.3f, 泊松比2=%.3f, 弹模1=%.3f, 弹模2=%.3f\n", sn[4], sn[5], sn[6], sn[7]);
    printf("      最小构造=%.3f, 最大构造=%.3f, Biot系数=%.3f\n", sn[8], sn[9], sn[10]);
    printf("输入文件: %s\n", filepath.c_str());
    printf("输出目录: %s\n", workpath.c_str());
    // 读取数据
    Matrix lasdata;
    if (!readLasData(filepath, lasdata)) {
        std::cerr << "Failed to open/read input file: " << filepath << "\n";
        return 1;
    }
    if (lasdata.empty()) {
        std::cerr << "Empty input data.\n";
        return 1;
    }

    // 过滤缺失：任一 [1],[2],[3],[4] <= nodata 则丢弃（与原逻辑一致）
    Matrix newlasdata;
    newlasdata.reserve(lasdata.size());
    for (const auto& r : lasdata) {
        if (r[1] <= nodata || r[2] <= nodata || r[3] <= nodata || r[4] <= nodata) continue;
        newlasdata.push_back(r);
    }
    if (newlasdata.size() < 2) {
        std::cerr << "Not enough valid rows after filtering.\n";
        return 1;
    }

    const size_t N = newlasdata.size();
    std::vector<double> shen; shen.reserve(N);
    std::vector<double> h;    h.reserve(N);
    std::vector<double> ya;   ya.reserve(N);
    std::vector<double> mpa, toi, pi, kxyl;
    std::vector<double> hb, hbbs, zbbs;
    std::vector<double> dtbsb, jtbsb, dtdxml, jtdxml;
    std::vector<double> qwa, qwb;

    // 深度、h
    shen.push_back(newlasdata[0][0]);
    h.push_back(0.0);
    double hx = 0.0;
    for (size_t i = 1; i < N; ++i) {
        shen.push_back(newlasdata[i][0]);
        hx += newlasdata[i][3] * G * (shen[i] - shen[i - 1]); // 密度列[3]
        h.push_back(hx);
    }

    // ya

    double den0 = newlasdata[0][3];
    for (size_t i = 0; i < N; ++i) {
        ya.push_back(((sn[0] + den0) * G * shen[0]) / 2.0 + h[i]);
    }

    // ln 回归：ln(y) = ln(d1) + d2 * (-shen)，仅 y>0
    long long n_valid = 0;
    long double sum_x2 = 0, sum_lny = 0, sum_x = 0, sum_xlny = 0;
    for (size_t i = 1; i < N; ++i) {
        double y = newlasdata[i][1];
        if (y <= 0) continue;
        long double x = -(long double)shen[i];
        long double lny = std::log((long double)y);
        sum_x2   += x * x;
        sum_lny  += lny;
        sum_x    += x;
        sum_xlny += x * lny;
        ++n_valid;
    }
    if (n_valid < 2) {
        std::cerr << "Not enough positive y-values for regression.\n";
        return 1;
    }
    long double denom = (long double)n_valid * sum_x2 - sum_x * sum_x;
    if (std::abs(denom) < 1e-18L) {
        std::cerr << "Regression denominator too small.\n";
        return 1;
    }
    long double ln_d1 = (sum_lny * sum_x2 - sum_x * sum_xlny) / denom;
    long double d2    = ((long double)n_valid * sum_xlny - sum_x * sum_lny) / denom;
    long double d1    = std::exp(ln_d1);
    printf("回归结果: d1=%.6Lf, d2=%.6Lf (y>0 共 %lld 点)\n", d1, d2, n_valid);
    // mpa、toi
    mpa.clear(); mpa.reserve(N);
    for (size_t i = 0; i < N; ++i) {
        mpa.push_back(rho_hydro * G * shen[i]);
    }

    toi.reserve(N);
    toi.push_back((double)(d1 * std::exp(d2 * (-(long double)shen[0]))));
    for (size_t i = 1; i < N; ++i) {
        // mpa.push_back(rho_hydro * G * shen[i]); // Eaton指数
        toi.push_back((double)(d1 * std::exp(d2 * (-(long double)shen[i]))));
    }

    // pi、kxyl
    pi.reserve(N); kxyl.reserve(N);
    for (size_t i = 0; i < N; ++i) {
        double toi_i = std::max(toi[i], 1e-18);
        double y1 = newlasdata[i][1];
        if (y1 <= 0) y1 = 1e-18;
        double val = newlasdata[i][3] - (newlasdata[i][3] - mpa[i]) * std::pow(y1 / toi_i, sn[1]);
        pi.push_back(val);
        kxyl.push_back(val / (shen[i] * G));
    }

    // hb/hbbs/zbbs
    hb.reserve(N); hbbs.reserve(N); zbbs.reserve(N);
    for (size_t i = 0; i < N; ++i) {
        double zbbs0 = 0.3048 * ONE_MILLION / newlasdata[i][1];
        double hbbs0 = sn[2] * zbbs0 + sn[3];
        zbbs.push_back(zbbs0);
        hbbs.push_back(hbbs0);
        double hb_i = (std::abs(hbbs0) < 1e-18) ? 0.0 : (ONE_MILLION * 0.3048) / hbbs0;
        hb.push_back(hb_i);
    }

    // dtbsb、jtbsb、dtdxml、jtdxml
    dtbsb.reserve(N); jtbsb.reserve(N); dtdxml.reserve(N); jtdxml.reserve(N);
    for (size_t i = 0; i < N; ++i) {
        double ss1 = hb[i] * hb[i];
        double ss2 = newlasdata[i][1] * newlasdata[i][1];
        double denom2 = 2.0 * (ss1 - ss2);
        double dt = (std::abs(denom2) < 1e-18) ? 0.0 : (ss1 - 2.0 * ss2) / denom2;
        dtbsb.push_back(dt);
        jtbsb.push_back(dt * sn[4] + sn[5]);

        double denom3 = ss1 * (ss1 - ss2);
        double dtd = (std::abs(denom3) < 1e-18) ? 0.0
                   : ((newlasdata[i][3]*(3.0 * ss1 - 4.0 * ss2) )/ (denom3 ) * 10000.0)/ std::pow(0.3047, 2.0);
        dtdxml.push_back(dtd);
        jtdxml.push_back(dtd * sn[6] + sn[7]);
    }

    // qwa/qwb
    qwa.reserve(N); qwb.reserve(N);
    for (size_t i = 0; i < N; ++i) {
        double ss5 = sn[10] * pi[i];
        double ss3 = ya[i] - ss5;
        double jt = jtbsb[i];
        double ss4 = (std::abs(1.0 - jt) < 1e-18) ? 0.0 : (jt / (1.0 - jt));
        qwa.push_back(ss4 * ss3 + sn[9] * ss3 + ss5); // 最大
        qwb.push_back(ss4 * ss3 + sn[8] * ss3 + ss5); // 最小
    }

    // 输出
    std::filesystem::path ipath(filepath);
    std::filesystem::path wpath(workpath);
    std::error_code ec;
    std::filesystem::create_directories(wpath, ec);
    if (ec) {
        std::cerr << "Failed to create work dir: " << workpath << " : " << ec.message() << "\n";
        return 1;
    }
    std::string outname = ipath.stem().string() + ".txt";
    std::filesystem::path outpath = wpath / outname;

    std::ofstream out(outpath, std::ios::binary);
    if (!out) {
        std::cerr << "Failed to open output file: " << outpath << "\n";
        return 1;
    }
    out.setf(std::ios::fixed); out << std::setprecision(std::max(0, prec));
    out << "#DEPT\t#最大主应力\t#最小主应力\n";
    for (size_t i = 0; i < N; ++i) {
        out << shen[i] << '\t' << qwa[i] << '\t' << qwb[i] << '\n';
    }
    out.close();

    std::cout << outpath.string() << "  单井地应力输出完成\n";
    return 0;
}
