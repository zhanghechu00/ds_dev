#include <iostream>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <vector>
#include <map>
#include <string>
#include <limits>
#include <cmath>
#include <cstdlib>
#include <filesystem>

void help(const char *pname)
{
    std::cout << "Usage: " << pname << " -o output.grdecl [options]\n";
    std::cout << "Options:\n";
    std::cout << "  -o, --output        输出文件名 (必选)\n";
    std::cout << "  --deformation       地形扰动强度 (默认0.5)\n";
    std::cout << "  --mapfile           地形控制图文件 (可选)\n";
    std::cout << "  --horizons          地层面文件 (可选)\n";
    std::cout << "  --xmin              X最小值 (默认0)\n";
    std::cout << "  --xmax              X最大值 (默认300)\n";
    std::cout << "  --ymin              Y最小值 (默认0)\n";
    std::cout << "  --ymax              Y最大值 (默认300)\n";
    std::cout << "  --zmin              Z最小值 (默认0)\n";
    std::cout << "  --zmax              Z最大值 (默认300)\n";
    std::cout << "  --lnx               X区间起点 (默认0)\n";
    std::cout << "  --rnx               X区间终点 (默认60)\n";
    std::cout << "  --lny               Y区间起点 (默认0)\n";
    std::cout << "  --rny               Y区间终点 (默认60)\n";
    std::cout << "  --lnz               Z区间起点 (默认0)\n";
    std::cout << "  --rnz               Z区间终点 (默认60)\n";
    std::cout << "  --refx              X细化倍数 (默认1)\n";
    std::cout << "  --refy              Y细化倍数 (默认1)\n";
    std::cout << "  --refz              Z细化倍数 (默认1)\n";
    std::cout << "  --wtk               VTK输出类型(默认1)\n";
    std::cout << "  --scalex            X缩放(默认1)\n";
    std::cout << "  --scaley            Y缩放(默认1)\n";
    std::cout << "  --scalez            Z缩放(默认1)\n";
    std::cout << "  --ecl               是否输出GRDECL(默认1)\n";
    std::cout << "  --permt             渗透率类型(默认0)\n";
    std::cout << "  --prec              输出精度(默认-1)\n";
    std::cout << "\nExample:\n";
    std::cout << "  " << pname << " -o output.grdecl --deformation 0.3 --rnx 30 --rny 100\n";
}

std::map<std::string, std::string> parseCommandLine(int argc, char *argv[])
{
    std::map<std::string, std::string> opts;
    for (int i = 1; i < argc; ++i)
    {
        std::string arg = argv[i];
        if (arg == "-h" || arg == "--help")
        {
            help(argv[0]);
            break;
        }
        if (arg[0] == '-' && arg[1] == '-')
        {
            std::string key = arg.substr(2);
            std::string val = std::string(argv[++i]);
            opts[key] = val;
        }
        else if (arg[0] == '-' && arg[1] == 'o')
        {
            std::string key = "output";
            std::string val = std::string(argv[++i]);
            opts[key] = val;
        }
    }
    return opts;
}

bool checkCommands(const std::map<std::string, std::string> &opts)
{
    if (opts.count("output") < 1)
    {
        return false;
    }

    return true;
}

template <class T>
T parseValue(const std::map<std::string, std::string> &opts, const std::string &key, T default_value)
{
    if (opts.count(key) < 1)
    {
        return default_value;
    }

    const std::string &val = opts.at(key);
    std::istringstream iss(val);
    T result;

    if constexpr (std::is_same<T, int>::value)
    {
        try
        {
            result = std::stoi(val);
        }
        catch (...)
        {
            return default_value;
        }
    }
    else if constexpr (std::is_same<T, float>::value)
    {
        try
        {
            result = std::stof(val);
        }
        catch (...)
        {
            return default_value;
        }
    }
    else if constexpr (std::is_same<T, double>::value)
    {
        try
        {
            result = std::stod(val);
        }
        catch (...)
        {
            return default_value;
        }
    }
    else if constexpr (std::is_same<T, bool>::value)
    {
        try
        {
            result = bool(std::stoi(val));
        }
        catch (...)
        {
            return default_value;
        }
    }
    else if constexpr (std::is_same<T, char *>::value || std::is_same<T, const char *>::value)
    {
        try
        {
            result = val.c_str();
        }
        catch (...)
        {
            return default_value;
        }
    }
    else
    {
        static_assert(std::is_same<T, int>::value || std::is_same<T, float>::value || std::is_same<T, double>::value,
                      "Unsupported type for parseValue");
    }

    return result;
}

#define ind(r, c) ((r) * N + (c))
void rand2d(double *arr, int N, int Nl, int Nr, int Nb, int Nt, double t)
{
    const double noind = std::numeric_limits<double>::max();
    // std::cout << "Nl:Nr " << Nl <<":" << Nr << " Nb:Nt " << Nb << ":" << Nt << std::endl;
    if (Nr - Nl < 2 && Nt - Nb < 2)
    {
        // std::cout << "exit" << std::endl;
        return;
    }
    // const double t = 0.15;
    int Nk = (Nb + Nt) / 2;
    int Nm = (Nl + Nr) / 2;
    // std::cout << "Nk " << Nk << " Nm " << Nm << std::endl;
    double lb = arr[ind(Nb, Nl)];
    double rb = arr[ind(Nb, Nr)];
    double lt = arr[ind(Nt, Nl)];
    double rt = arr[ind(Nt, Nr)];
    if (lb != lb || rb != rb || lt != lt || rt != rt)
        throw -1;
    if (arr[ind(Nk, Nl)] == noind)
        arr[ind(Nk, Nl)] = 0.5 * (lb + lt) + (2 * (rand() * 1.0 / RAND_MAX) - 1) * t;
    if (arr[ind(Nk, Nr)] == noind)
        arr[ind(Nk, Nr)] = 0.5 * (rb + rt) + (2 * (rand() * 1.0 / RAND_MAX) - 1) * t;
    if (arr[ind(Nb, Nm)] == noind)
        arr[ind(Nb, Nm)] = 0.5 * (lb + rb) + (2 * (rand() * 1.0 / RAND_MAX) - 1) * t;
    if (arr[ind(Nt, Nm)] == noind)
        arr[ind(Nt, Nm)] = 0.5 * (lt + rt) + (2 * (rand() * 1.0 / RAND_MAX) - 1) * t;
    arr[ind(Nk, Nm)] = 0.25 * (lb + rb + lt + rt) + (2 * (rand() * 1.0 / RAND_MAX) - 1) * t;
    rand2d(arr, N, Nl, Nm, Nb, Nk, t * 0.5);
    rand2d(arr, N, Nm, Nr, Nb, Nk, t * 0.5);
    rand2d(arr, N, Nl, Nm, Nk, Nt, t * 0.5);
    rand2d(arr, N, Nm, Nr, Nk, Nt, t * 0.5);
}

void init2d(double *arr, int N, double mint, double maxt)
{
    for (int k = 0; k < N * N; ++k)
        arr[k] = std::numeric_limits<double>::max();
    arr[ind(0, 0)] = mint + (rand() * 1.0 / RAND_MAX) * (maxt - mint);
    arr[ind(0, N - 1)] = mint + (rand() * 1.0 / RAND_MAX) * (maxt - mint);
    arr[ind(N - 1, 0)] = mint + (rand() * 1.0 / RAND_MAX) * (maxt - mint);
    arr[ind(N - 1, N - 1)] = mint + (rand() * 1.0 / RAND_MAX) * (maxt - mint);
}
std::vector<double> readHorizonData(const std::string &horizons_file, int &nz)
{
    std::vector<double> horizons;
    if (!horizons_file.empty())
    {
        std::ifstream fhorizons(horizons_file);
        if (fhorizons.fail())
        {
            std::cout << "Error: cannot open horizons file: " << horizons_file << std::endl;
            return horizons;
        }
        double zval;
        while (fhorizons >> zval)
        {
            horizons.push_back(zval);
        }
        fhorizons.close();

        if (horizons.size() < 2)
        {
            std::cout << "Error: horizons file 必须至少包含两个Z坐标！" << std::endl;
            return horizons;
        }
        std::cout << "成功读取层界面数: " << horizons.size() << std::endl;
        nz = horizons.size() - 1;
        std::cout << "nz值重新设定为：  " << nz << std::endl;
    }

    return horizons;
}

std::vector<double> createMapMat(const std::string &mapfile, int &N, double deformation)
{
    std::vector<double> map_mat;
    if (!mapfile.empty())
    {
        // 读取外部 map 文件
        std::ifstream fmap(mapfile);
        if (fmap.fail())
        {
            std::cout << "Error: cannot open map file: " << mapfile << std::endl;
            return map_mat;
        }
        std::string line;
        while (std::getline(fmap, line))
        {
            if (line.empty()) // 跳过空行和注释行
                continue;
            std::istringstream iss(line);
            double x = 0.0, y = 0.0, h = 0.0;
            iss >> x >> y >> h;
            map_mat.push_back(h);
        }
        fmap.close();

        std::size_t count = map_mat.size();
        int root = static_cast<int>(std::sqrt(count));
        if (root * root != count)
        {
            std::cout << "Error: map.txt 数据量不是平方数，无法识别为 N×N！" << std::endl;
            map_mat.clear();
        }
        N = root;
        std::cout << "map.txt 自动识别到 N = " << N << std::endl;
        // 先要将-9999的内容替换位一行中最近的有效值
        // 再要做一个归一化
        if (N > 0)
        {
            for (int row = 0; row < N; ++row)
            {
                double last_valid = std::numeric_limits<double>::quiet_NaN();
                for (int col = 0; col < N; ++col)
                {
                    int idx = row * N + col;
                    if (map_mat[idx] > -9998.0)
                        last_valid = map_mat[idx];
                    else if (last_valid == last_valid)
                        map_mat[idx] = last_valid; // 前向
                }
                last_valid = std::numeric_limits<double>::quiet_NaN();
                for (int col = N - 1; col >= 0; --col)
                {
                    int idx = row * N + col;
                    if (map_mat[idx] > -9998.0)
                        last_valid = map_mat[idx];
                    else if (last_valid == last_valid)
                        map_mat[idx] = last_valid; // 后向
                }
            }
            std::cout << "异常值处理完成，所有 -9999 已被填充。\n";
            {
                std::ofstream mout("processed_map.txt");
                if (mout)
                {
                    for (int row = 0; row < N; ++row)
                        for (int col = 0; col < N; ++col)
                            mout << map_mat[row * N + col] << '\n';
                    std::cout << "已导出处理后的 map 到 processed_map.txt\n";
                }
            }
            double minv = map_mat[0], maxv = map_mat[0];
            for (int i = 1; i < N * N; ++i)
            {
                minv = std::min(minv, map_mat[i]);
                maxv = std::max(maxv, map_mat[i]);
            }
            double range = maxv - minv;
            std::cout << "高度值范围: [" << minv << ", " << maxv << "]\n";
            if (range > 0)
            {
                for (int i = 0; i < N * N; ++i)
                    map_mat[i] = (map_mat[i] - minv) / range;
                std::cout << "map 已归一化到 [0,1]\n";
            }
            else
            {
                std::cerr << "Warning: 所有高度值相同，跳过归一化。\n";
            }
        }
    }
    else
    {
        // 继续使用原有的随机 map 生成方式
        map_mat.resize(N * N, 0.0);
        init2d((double *)map_mat.data(), N, 0.0, deformation);
        rand2d((double *)map_mat.data(), N, 0, N - 1, 0, N - 1, deformation * 0.5);
        // ... 可以继续加断层构造等 ...
    }

    return map_mat;
}

int wrap(int i, int n)
{
    if ((i / n) % 2 == 0)
        return i % n;
    else
        return n - 1 - i % n;
}

double wrapx(double x)
{
    if (((int)floor(x)) % 2 == 0)
        return x - floor(x);
    else
        return 1.0 - (x - floor(x));
}

double intrp2d(const double *arr, int N, double x, double y)
{
    int n = (int)ceil(x * (N - 1));
    int m = (int)ceil(y * (N - 1));
    if (n == 0)
        n = 1;
    if (m == 0)
        m = 1;
    double dh = 1.0 / (double)(N - 1);
    double kx = (x - (n - 1) * dh) / dh;
    double ky = (y - (m - 1) * dh) / dh;
    // if( kx < 0 || kx > 1 ) std::cout << "bad kx: " << kx << " x is " << x << " n is " << n << " dh is " << dh << " N is " << N << std::endl;
    // if( ky < 0 || ky > 1 ) std::cout << "bad ky: " << ky << " y is " << y << " m is " << m << " dh is " << dh << " N is " << N << std::endl;
    double lb = arr[ind(m - 1, n - 1)];
    double rb = arr[ind(m - 1, n + 0)];
    double lt = arr[ind(m + 0, n - 1)];
    double rt = arr[ind(m + 0, n + 0)];
    if (lb != lb || rb != rb || lt != lt || rt != rt)
        throw -1;
    return (1 - ky) * (lb * (1 - kx) + rb * kx) + ky * (lt * (1 - kx) + rt * kx);
}

double intrp2dx(const double *arr, int N, double x, double y)
{
    int n = (int)ceil(x * (N - 1));
    int m = (int)ceil(y * (N - 1));
    if (n == 0)
        n = 1;
    if (m == 0)
        m = 1;
    double dh = 1.0 / (double)(N - 1);
    double lb = arr[ind(m - 1, n - 1)];
    double rb = arr[ind(m - 1, n + 0)];
    double lt = arr[ind(m + 0, n - 1)];
    double rt = arr[ind(m + 0, n + 0)];
    return 0.5 * ((rt + rb) - (lt + lb)) / dh;
}

double intrp2dy(const double *arr, int N, double x, double y)
{
    int n = (int)ceil(x * (N - 1));
    int m = (int)ceil(y * (N - 1));
    if (n == 0)
        n = 1;
    if (m == 0)
        m = 1;
    double dh = 1.0 / (double)(N - 1);
    double lb = arr[ind(m - 1, n - 1)];
    double rb = arr[ind(m - 1, n + 0)];
    double lt = arr[ind(m + 0, n - 1)];
    double rt = arr[ind(m + 0, n + 0)];
    return 0.5 * ((rt + lt) - (rb + lb)) / dh;
}

void normalize(double n[3])
{
    double l;
    l = std::sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2]);
    if (l)
    {
        n[0] /= l;
        n[1] /= l;
        n[2] /= l;
    }
}

void transform(const double *map, double xyz[3], const double max[3], const double min[3], double &ztop, double &zbottom, double nrmtop[3], double nrmbottom[3], int N)
{
    double x = (xyz[0] - min[0]) / (max[0] - min[0]), y = (xyz[1] - min[1]) / (max[1] - min[1]), z = (xyz[2] - min[2]) / (max[2] - min[2]);
    x = wrapx(x);
    y = wrapx(y);
    z = wrapx(z);
    if (x < 0 || x > 1)
    {
        throw -1;
        std::cout << "x: " << x << " xyz " << xyz[0] << " " << xyz[1] << " " << xyz[2] << " unit " << x << " " << y << " " << z << " min " << min[0] << " " << min[1] << " " << min[2] << " max " << max[0] << " " << max[1] << " " << max[2] << std::endl;
    }
    if (y < 0 || y > 1)
        std::cout << "y: " << y << " xyz " << xyz[0] << " " << xyz[1] << " " << xyz[2] << " unit " << x << " " << y << " " << z << " min " << min[0] << " " << min[1] << " " << min[2] << " max " << max[0] << " " << max[1] << " " << max[2] << std::endl;
    if (z < 0 || z > 1)
        std::cout << "z: " << z << " xyz " << xyz[0] << " " << xyz[1] << " " << xyz[2] << " unit " << x << " " << y << " " << z << " min " << min[0] << " " << min[1] << " " << min[2] << " max " << max[0] << " " << max[1] << " " << max[2] << std::endl;
    double dztopdx = 0, dztopdy = 0;
    double dzbottomdx = 0, dzbottomdy = 0;
    double shift = 0;
    // zbottom = x*x*4-y*y*4-sin(6*x)*8 - cos(4*y)*4 - x*15;
    // ztop = x*x*4-y*y*4-sin(6*x)*8 - cos(4*y)*4 - y*15 + 15;

    // zbottom = std::sin(y*pi *2)*0.2;// ((x - 0.5)*(x - 0.5) + (y - 0.5)*(y - 0.5))*0.4;
    // ztop = std::sin(y*pi *2)*0.2+1;// 1 + cos(4 * y)*0.2 + ((x - 0.5)*(x - 0.5) + (y - 0.5)*(y - 0.5))*0.4 + 1 + cos(4 * y)*0.5;
    // dzbottomdx = 0;
    // dzbottomdy = 2*pi*std::cos(y*pi*2)*0.2;
    // dztopdx = 0;
    // dztopdy = 2*pi*std::cos(y*pi*2)*0.2;

    shift = intrp2d(map, N, x, y);
    zbottom = shift;
    ztop = 1 + shift;
    dzbottomdx = dztopdx = intrp2dx(map, N, x, y);
    dzbottomdy = dztopdy = intrp2dy(map, N, x, y);

    // zbottom = 0;// ((x-0.5)*(x-0.5) + (y-0.5)*(y-0.5))*0.4;
    // ztop = 1 + 1*y;//cos(4*y)*0.2;// + ((x-0.5)*(x-0.5) + (y-0.5)*(y-0.5))*0.4 + 1 + cos(4*y)*0.5;

    // zbottom = 0;// ((x-0.5)*(x-0.5) + (y-0.5)*(y-0.5))*0.4;
    // ztop = 1 + cos(4*y)*0.2;// + ((x-0.5)*(x-0.5) + (y-0.5)*(y-0.5))*0.4 + 1 + cos(4*y)*0.5;

    nrmtop[0] = dztopdx;
    nrmtop[1] = dztopdy;
    nrmtop[2] = -1;
    normalize(nrmtop);
    nrmbottom[0] = dzbottomdx;
    nrmbottom[1] = dzbottomdy;
    nrmbottom[2] = -1;
    normalize(nrmbottom);
}

void changexyz(double xyz[3], double max[3], double min[3], double ztop, double zbottom, double xyzout[3])
{
    double tz = (xyz[2] - min[2]) / (max[2] - min[2]), tznew;
    tznew = (ztop - zbottom) * tz + zbottom;
    xyzout[0] = xyz[0];
    xyzout[1] = xyz[1];
    xyzout[2] = tznew * (max[2] - min[2]) + min[2];
}

double ztop, zbottom, xyz[3], xyzout[3], nrmtop[3], nrmbottom[3], nrm[3], Kin[3], Kout[6];
double max[3] = {0, 0, 0}, min[3] = {0, 0, 0};

std::vector<double> ReadProData(const std::string &filename, int nz, int ny, int nx)
{
    std::vector<double> poro;
    double value = 0.0;
    std::ifstream fporo(filename);
    if (fporo.fail())
    {
        std::cout << "SPE10 data files not found." << std::endl;
        std::cout << "Expecting spe_phi.dat." << std::endl;
    }
    else
    {
        poro.reserve(nz * ny * nx);
        for (int k = 0; k < nz; ++k)
        {
            for (int j = 0; j < ny; ++j)
            {
                for (int i = 0; i < nx; ++i)
                {
                    fporo >> value;
                    // value = max(value, 1.0e-4);
                    value = std::min(value, 1.0);
                    poro.push_back(value);
                }
            }
        }
        fporo.close();
    }
    return poro;
}

struct quat
{
    double vec[3];
    double w;
};

double quatnorm(const quat &a)
{
    return a.vec[0] * a.vec[0] + a.vec[1] * a.vec[1] + a.vec[2] * a.vec[2] + a.w * a.w;
}

quat quatconj(const quat &a)
{
    quat ret = a;
    ret.vec[0] = -ret.vec[0];
    ret.vec[1] = -ret.vec[1];
    ret.vec[2] = -ret.vec[2];
    return ret;
}

void transposemxn(const double *a, double *b, int m, int n)
{
    for (int j = 0; j < m; j++)
    {
        for (int i = 0; i < n; i++)
            b[i * m + j] = a[j * n + i];
    }
}

void matmulmxnxk(const double *a, const double *b, double *out, int m, int n, int k)
{
    int i, j, l;
    for (i = 0; i < n; i++)
        for (j = 0; j < m; j++)
        {
            out[j * n + i] = 0.0;
            for (l = 0; l < k; l++)
                out[j * n + i] += a[j * k + l] * b[l * n + i];
        }
}

void rotate_tensor(double nrm[3], const double Kin[3], double Kout[6])
{
    double qmat[9], qmat_t[9], prod[9], qnrm;
    struct quat q, qr;

    q.vec[0] = -nrm[1];
    q.vec[1] = nrm[0];
    q.vec[2] = 0;
    q.w = 1.0 - nrm[2];

    qnrm = quatnorm(q);
    q.vec[0] /= qnrm;
    q.vec[1] /= qnrm;
    q.w /= qnrm;
    qr = quatconj(q);

    qmat[0] = (q.w * q.w + q.vec[0] * q.vec[0] - q.vec[1] * q.vec[1]) * qnrm;
    qmat[1] = 2. * (q.vec[0] * q.vec[1]) * qnrm;
    qmat[2] = 2. * (q.w * q.vec[1]) * qnrm;

    qmat[3] = 2. * (q.vec[0] * q.vec[1]) * qnrm;
    qmat[4] = (q.w * q.w - q.vec[0] * q.vec[0] + q.vec[1] * q.vec[1]) * qnrm;
    qmat[5] = 2. * (-q.w * q.vec[0]) * qnrm;

    qmat[6] = 2. * (-q.w * q.vec[1]) * qnrm;
    qmat[7] = 2. * (+q.w * q.vec[0]) * qnrm;
    qmat[8] = (q.w * q.w - q.vec[0] * q.vec[0] - q.vec[1] * q.vec[1]) * qnrm;

    transposemxn(qmat, qmat_t, 3, 3);

    qmat[0] *= Kin[0];
    qmat[1] *= Kin[0];
    qmat[2] *= Kin[0];

    qmat[3] *= Kin[1];
    qmat[4] *= Kin[1];
    qmat[5] *= Kin[1];

    qmat[6] *= Kin[2];
    qmat[7] *= Kin[2];
    qmat[8] *= Kin[2];

    matmulmxnxk(qmat_t, qmat, prod, 3, 3, 3);

    Kout[0] = prod[0];
    Kout[1] = prod[1];
    Kout[2] = prod[2];
    Kout[3] = prod[4];
    Kout[4] = prod[5];
    Kout[5] = prod[8];
}

bool ReadPermData(const std::string &filename,
                  int nz, int ny, int nx,
                  std::vector<std::vector<double>> &perm,
                  std::vector<std::vector<double>> &permnew,
                  int permt,
                  double scalex, double scaley, double scalez,
                  const std::vector<double> &map, int N)
{
    double *map_data = (const_cast<double *>(map.data()));
    double value = 0.0;
    std::ifstream fperm(filename);
    if (fperm.fail())
    {
        std::cout << "SPE10 data files not found." << std::endl;
        std::cout << "Expecting spe_perm.dat." << std::endl;
        return false;
    }
    else
    {
        perm.resize(3);
        permnew.resize(6);
        for (int l = 0; l < 3; ++l)
        {
            perm[l].reserve(nz * ny * nx);
            for (int k = 0; k < nz; ++k)
            {
                for (int j = 0; j < ny; ++j)
                {
                    for (int i = 0; i < nx; ++i)
                    {
                        fperm >> value;
                        perm[l].push_back(value);
                    }
                }
            }
        }
        fperm.close();

        if (permt == 1)
        {
            for (int l = 0; l < 6; ++l)
                permnew[l].reserve(nx * ny * nz);

            int nout = 0;
            for (int k = 0; k < nz; ++k)
            {
                for (int j = 0; j < ny; ++j)
                {
                    for (int i = 0; i < nx; ++i)
                    {
                        xyz[0] = 240.0 * scalex * (i + 0.5) / 60.0;
                        xyz[1] = 440.0 * scaley * (j + 0.5) / 220.0;
                        xyz[2] = 340.0 * scalez * (k + 0.5) / 85.0;
                        Kin[0] = perm[0][nout];
                        Kin[1] = perm[1][nout];
                        Kin[2] = perm[2][nout];
                        transform(map_data, xyz, max, min, ztop, zbottom, nrmtop, nrmbottom, N);
                        for (int l = 0; l < 3; ++l)
                            nrm[l] = (nrmtop[l] - nrmbottom[l]) * (xyz[2] - min[2]) / (max[2] - min[2]) + nrmbottom[l];
                        rotate_tensor(nrm, Kin, Kout);
                        for (int l = 0; l < 6; ++l)
                            permnew[l].push_back(Kout[l]);
                        nout++;
                    }
                }
            }
        }
    }
    return 0;
}

const std::vector<double> &findClosestWellData(const std::map<double, std::vector<double>> &well_data,
                                               double z)
{
    auto it = well_data.lower_bound(z); // 第一个 >= target 的迭代器
    if (it == well_data.begin())
    {
        // target 比所有 key 都小
        return it->second; // 返回第一个元素的值
    }
    else if (it == well_data.end())
    {
        // target 比所有 key 都大
        return well_data.rbegin()->second;
    }
    else
    {
        // 比较 it 和前一个
        auto prev = std::prev(it);
        if (std::fabs(it->first - z) < std::fabs(prev->first - z))
        {
            return it->second;
        }
        else
        {
            return prev->second;
        }
    }
}
int writeECL(const std::string &ecl_name, int prec,
             double scalex, double scaley, double scalez,
             int lnx, int rnx, int lny, int rny, int lnz, int rnz,
             int refx, int refy, int refz, int N, int nz, int ny, int nx,
             double xmin, double xmax, double ymin, double ymax, double zmin, double zmax,
             std::vector<double> &map, std::size_t &nout, std::vector<double> &poro,
             std::map<double, std::vector<double>> &well_data,
             std::vector<std::string> &well_properties)
{
    printf("Writing ECL file: %s\n", ecl_name.c_str());
    printf("  lnx: %d, rnx: %d, lny: %d, rny: %d, lnz: %d, rnz: %d\n", lnx, rnx, lny, rny, lnz, rnz);
    printf("  refx: %d, refy: %d, refz: %d\n", refx, refy, refz);
    printf("  scalex: %f, scaley: %f, scalez: %f\n", scalex, scaley, scalez);
    double lenthx = abs(xmax - xmin), lenthy = abs(ymax - ymin), lenthz = abs(zmax - zmin);
    printf("  lenthx: %f, lenthy: %f, lenthz: %f\n", lenthx, lenthy, lenthz);
    double max[3] = {lenthx * scalex, lenthy * scaley, lenthz * scalez}, min[3] = {0, 0, 0};
    printf("  min: %f %f %f, max: %f %f %f\n", min[0], min[1], min[2], max[0], max[1], max[2]);
    double Thickness = 500;

    // max[0] = 300 * scalex;
    // max[1] = 300 * scaley;
    // max[2] = 300 * scalez;
    double *map_data = map.data();
    std::ofstream f;
    std::cout << "Opening " << ecl_name << " for output." << std::endl;
    f.open(ecl_name.c_str());
    if (f.fail())
    {
        std::cout << "Cannot open " << ecl_name << " for writing!" << std::endl;
        return -1;
    }
    if (prec > 0)
        f << std::setprecision(prec);

    std::cout << "intervals x " << lnx << ":" << rnx << " y " << lny << ":" << rny << " " << lnz << ":" << rnz << std::endl;
    std::cout << "refinement x " << refx << " y " << refy << " z " << refz << std::endl;
    std::cout << "Writing grid data." << std::endl;

    f << "DIMENS" << std::endl;
    f << (rnx - lnx) * refx << " " << (rny - lny) * refy << " " << (rnz - lnz) * refz << std::endl;
    f << "/" << std::endl;

    f << "SPECGRID" << std::endl;
    f << (rnx - lnx) * refx << " " << (rny - lny) * refy << " " << (rnz - lnz) * refz << " " << 1 << " " << 'P' << std::endl;
    f << "/" << std::endl;

    f << "COORD" << std::endl;
    double xyzb[3], xyzt[3];
    double mid_b = 0.0, mid_t = 0.0;
    for (int j = lny; j <= rny; ++j)
    {
        for (int jr = 0; jr < (j < rny ? refy : 1); jr++)
        {
            for (int i = lnx; i <= rnx; ++i)
            {
                for (int ir = 0; ir < (i < rnx ? refx : 1); ir++)
                {
                    // bottom point
                    xyzb[0] = xyzt[0] = max[0] * (i * 1. * refx + ir) / (nx * refx);
                    xyzb[1] = xyzt[1] = max[1] * (j * 1. * refy + jr) / (ny * refy);
                    xyzb[2] = 0;
                    transform(map_data, xyzb, max, min, ztop, zbottom, nrmtop, nrmbottom, N);
                    changexyz(xyzb, max, min, ztop, zbottom, xyzout);
                    xyzout[0] = xmin+xyzout[0];
                    xyzout[1] = ymin+xyzout[1];
                    xyzout[2] = zmin+xyzout[2];
                    f << std::fixed << std::setprecision(4)<< xyzout[0] << " " << xyzout[1] << " " << xyzout[2];
                    f << " ";
                    if (j == int(rny / 2) && i == int(rnx / 2))
                    {
                        mid_b = xyzout[2];
                    }
                    // top point
                    xyzt[2] = max[2];
                    transform(map_data, xyzt, max, min, ztop, zbottom, nrmtop, nrmbottom, N);
                    changexyz(xyzt, max, min, ztop, zbottom, xyzout);
                    xyzout[0] = xmin+xyzout[0];
                    xyzout[1] = ymin+xyzout[1];
                    xyzout[2] = zmin+xyzout[2];
                    f << std::fixed << std::setprecision(4)<<xyzout[0] << " " << xyzout[1] << " " << xyzout[2];
                    f << std::endl;
                    if (j == int(rny / 2) && i == int(rnx / 2))
                    {
                        mid_t = xyzout[2];
                    }
                }
            }
        }
    }
    f << "/" << std::endl;
    std::cout << "find mid z point is " << mid_b << " and " << mid_t << std::endl;
    f << "ZCORN" << std::endl;
    nout = 0;
    for (int k = lnz; k < rnz; ++k)
    {
        for (int kr = 0; kr < refz; ++kr)
        {
            // top corners
            xyz[2] = Thickness * scalez * (k * 1. * refz + kr) / (nz * refz);
            for (int j = lny; j < rny; ++j)
            {
                for (int jr = 0; jr < refy; ++jr)
                {
                    xyz[1] = lenthy * scaley * (j * 1. * refy + jr) / (ny * refy);
                    // top corners, near left and near right
                    for (int i = lnx; i < rnx; ++i)
                    {
                        for (int ir = 0; ir < refx; ++ir)
                        {
                            // top near left corner
                            xyz[0] = lenthx * scalex * (i * 1. * refx + ir) / (nx * refx);
                            transform(map_data, xyz, max, min, ztop, zbottom, nrmtop, nrmbottom, N);
                            changexyz(xyz, max, min, ztop, zbottom, xyzout);
                            xyzout[0] = xmin+xyzout[0];
                            xyzout[1] = ymin+xyzout[1];
                            xyzout[2] = zmin+xyzout[2];
                            f << std::fixed << std::setprecision(4)<<xyzout[2] << " ";
                            // top near right corner
                            xyz[0] = lenthx * scalex * (i * 1. * refx + ir + 1) / (nx * refx);
                            transform(map_data, xyz, max, min, ztop, zbottom, nrmtop, nrmbottom, N);
                            changexyz(xyz, max, min, ztop, zbottom, xyzout);
                            xyzout[0] = xmin+xyzout[0];
                            xyzout[1] = ymin+xyzout[1];
                            xyzout[2] = zmin+xyzout[2];
                            f << std::fixed << std::setprecision(4)<<xyzout[2] << " ";
                            nout++;
                            if (nout % 5 == 0)
                                f << std::endl;
                        }
                    }
                    xyz[1] = lenthy * scaley * (j * 1. * refy + jr + 1) / (ny * refy);
                    // top corners, far left and far right
                    for (int i = lnx; i < rnx; ++i)
                    {
                        for (int ir = 0; ir < refx; ++ir)
                        {
                            // top far left corner
                            xyz[0] = lenthx * scalex * (i * 1. * refx + ir) / (nx * refx);
                            transform(map_data, xyz, max, min, ztop, zbottom, nrmtop, nrmbottom, N);
                            changexyz(xyz, max, min, ztop, zbottom, xyzout);
                            xyzout[0] = xmin+xyzout[0];
                            xyzout[1] = ymin+xyzout[1];
                            xyzout[2] = zmin+xyzout[2];

                            f << std::fixed << std::setprecision(4)<<xyzout[2] << " ";
                            // top far right corner
                            xyz[0] = lenthx * scalex * (i * 1. * refx + ir + 1) / (nx * refx);
                            transform(map_data, xyz, max, min, ztop, zbottom, nrmtop, nrmbottom, N);
                            changexyz(xyz, max, min, ztop, zbottom, xyzout);
                            xyzout[0] = xmin+xyzout[0];
                            xyzout[1] = ymin+xyzout[1];
                            xyzout[2] = zmin+xyzout[2];
                            f << std::fixed << std::setprecision(4)<<xyzout[2] << " ";
                            nout++;
                            if (nout % 5 == 0)
                                f << std::endl;
                        }
                    }
                }
            }
            xyz[2] = Thickness * scalez * (k * 1. * refz + kr + 1) / (nz * refz);
            // bottom corners
            for (int j = lny; j < rny; ++j)
            {
                for (int jr = 0; jr < refy; ++jr)
                {
                    xyz[1] = lenthy * scaley * (j * 1. * refy + jr) / (ny * refy);
                    // top corners, near left and near right
                    for (int i = lnx; i < rnx; ++i)
                    {
                        for (int ir = 0; ir < refx; ++ir)
                        {
                            // bottom near left corner
                            xyz[0] = lenthx * scalex * (i * 1. * refx + ir) / (nx * refx);
                            transform(map_data, xyz, max, min, ztop, zbottom, nrmtop, nrmbottom, N);
                            changexyz(xyz, max, min, ztop, zbottom, xyzout);
                            xyzout[0] = xmin+xyzout[0];
                            xyzout[1] = ymin+xyzout[1];
                            xyzout[2] = zmin+xyzout[2];
                            f << std::fixed << std::setprecision(4)<< xyzout[2] << " ";
                            // bottom near right corner
                            xyz[0] = lenthx * scalex * (i * 1. * refx + ir + 1) / (nx * refx);
                            transform(map_data, xyz, max, min, ztop, zbottom, nrmtop, nrmbottom, N);
                            changexyz(xyz, max, min, ztop, zbottom, xyzout);
                            xyzout[0] = xmin+xyzout[0];
                            xyzout[1] = ymin+xyzout[1];
                            xyzout[2] = zmin+xyzout[2];

                            f << std::fixed << std::setprecision(4)<< xyzout[2] << " ";
                            nout++;
                            if (nout % 5 == 0)
                                f << std::endl;
                        }
                    }
                    xyz[1] = lenthy * scaley * (j * 1. * refy + jr + 1) / (ny * refy);
                    // top corners, far left and far right
                    for (int i = lnx; i < rnx; ++i)
                    {
                        for (int ir = 0; ir < refx; ++ir)
                        {
                            // bottom far left corner
                            xyz[0] = lenthx * scalex * (i * 1. * refx + ir) / (nx * refx);
                            transform(map_data, xyz, max, min, ztop, zbottom, nrmtop, nrmbottom, N);
                            changexyz(xyz, max, min, ztop, zbottom, xyzout);
                            xyzout[0] = xmin+xyzout[0];
                            xyzout[1] = ymin+xyzout[1];
                            xyzout[2] = zmin+xyzout[2];


                            f << std::fixed << std::setprecision(4)<< xyzout[2] << " ";
                            // bottom far right corner
                            xyz[0] = lenthx * scalex * (i * 1. * refx + ir + 1) / (nx * refx);
                            transform(map_data, xyz, max, min, ztop, zbottom, nrmtop, nrmbottom, N);
                            changexyz(xyz, max, min, ztop, zbottom, xyzout);
                            xyzout[0] = xmin+xyzout[0];
                            xyzout[1] = ymin+xyzout[1];
                            xyzout[2] = zmin+xyzout[2];

                            f << std::fixed << std::setprecision(4)<< xyzout[2] << " ";
                            nout++;
                            if (nout % 5 == 0)
                                f << std::endl;
                        }
                    }
                }
            }
        }
    }
    if (nout % 5 != 0)
        f << std::endl;
    f << "/" << std::endl;

    int nnz = (int)ceil(rnz / (double)nz);
    int nny = (int)ceil(rny / (double)ny);
    int nnx = (int)ceil(rnx / (double)nx);

    if (poro.size() > 0)
    {
        f << "PORO" << std::endl;
        for (int k = 0; k < nz * nnz; ++k)
        {
            for (int kr = 0; kr < refz; ++kr)
                for (int j = 0; j < ny * nny; ++j)
                {
                    for (int jr = 0; jr < refy; ++jr)
                        for (int i = 0; i < nx * nnx; ++i)
                        {
                            for (int ir = 0; ir < refx; ++ir)
                                if (i >= lnx && i < rnx &&
                                    j >= lny && j < rny &&
                                    k >= lnz && k < rnz)
                                {
                                    int ind = wrap(i, nx) + wrap(j, ny) * nx + wrap(k, nz) * nx * ny;
                                    f << poro[ind] << " ";
                                    nout++;
                                    if (nout % 10 == 0)
                                        f << std::endl;
                                }
                        }
                }
        }

        if (nout % 10 != 0)
            f << std::endl;
        f << "/" << std::endl;
    }

    std::map<int, std::vector<double>> well_data_map;
    printf("Writing well data.\n");

    for (int k = 0; k < nz; ++k)
    {
        double cur_z = Thickness / nz * k + mid_b;
        // printf("  Processing layer %d at z = %f\n", k + 1, cur_z);
        auto &well_data_at_z = findClosestWellData(well_data, cur_z);
        well_data_map[k] = well_data_at_z;
        // printf("    found data at z = %f\n", well_data_at_z[0]);
    }
    std::filesystem::path specific_path = ecl_name;
    // 获取父目录
    std::filesystem::path parent_path = specific_path.parent_path();


    for (std::size_t i = 0; i < well_properties.size(); i++)
    {
        std::string &well_property = well_properties[i];
        f << well_property << std::endl;
        std::filesystem::path wp = parent_path / (well_property + ".grdecl");
        std::ofstream out_prot(wp.string());
        out_prot << well_property << std::endl;
        nout = 0;
        {
            for (int j = 0; j < nz; ++j)
            {
                for (int k = 0; k < nx * ny; ++k)
                {
                    f << well_data_map[j][i + 1] << " ";
                    out_prot << well_data_map[j][i + 1] << " ";
                    nout++;
                    if (nout % 10 == 0)
                    {
                        f << std::endl;
                        out_prot << std::endl;
                    }
                }
            }
        }
        f << "/" << std::endl;
        out_prot << "/" << std::endl;
    }

    return 0;
}

int appendECL(const std::string &ecl_name, int prec, int permt,
              double scalex, double scaley, double scalez,
              int lnx, int rnx, int lny, int rny, int lnz, int rnz,
              int nx, int ny, int nz,
              int refx, int refy, int refz,
              std::vector<std::vector<double>> &perm,
              std::vector<std::vector<double>> &permnew)
{
    int nnz = (int)ceil(rnz / (double)nz);
    int nny = (int)ceil(rny / (double)ny);
    int nnx = (int)ceil(rnx / (double)nx);
    std::ofstream f;
    std::cout << "Opening " << ecl_name << " for output." << std::endl;
    f.open(ecl_name.c_str(), std::ios::app);
    if (f.fail())
    {
        std::cout << "Cannot open " << ecl_name << " for writing!" << std::endl;
        return -1;
    }

    const int nl[3] = {3, 6, 1};
    int nout = 0;
    if (permnew.size() < 1)
    {
        std::cout << "No perm data to write!" << std::endl;
        return -1;
    }
    {
        if (permt == 1)
        {
            f << "MPFA" << std::endl;
            f << 1 << " " << 0 << std::endl; // define tensor in x,y,z coords and use TPFA
            f << "/" << std::endl;
        }
        const char c1[6] = {'X', 'X', 'X', 'Y', 'Y', 'Z'};
        const char c2[6] = {'X', 'Y', 'Z', 'Y', 'Z', 'Z'};
        for (int l = 0; l < nl[permt]; ++l)
        {
            if (permt == 0)
                f << "PERM" << c2[l] << std::endl;
            else if (permt == 1)
                f << "PERM" << c1[l] << c2[l] << std::endl;
            else if (permt == 2)
                f << "PERM" << std::endl;
            nout = 0;
            for (int k = 0; k < nz * nnz; ++k)
            {
                for (int kr = 0; kr < refz; ++kr)
                    for (int j = 0; j < ny * nny; ++j)
                    {
                        for (int jr = 0; jr < refy; ++jr)
                            for (int i = 0; i < nx * nnx; ++i)
                            {
                                for (int ir = 0; ir < refx; ++ir)
                                    if (i >= lnx && i < rnx &&
                                        j >= lny && j < rny &&
                                        k >= lnz && k < rnz)
                                    {
                                        int ind = wrap(i, nx) + wrap(j, ny) * nx + wrap(k, nz) * nx * ny;
                                        if (permt == 0)
                                            f << perm[l][ind] << " ";
                                        else if (permt == 1)
                                            f << permnew[l][ind] << " ";
                                        else if (permt == 2)
                                            f << sqrt(pow(perm[0][ind], 2) + pow(perm[1][ind], 2) + pow(perm[2][ind], 2));
                                        nout++;
                                        if (nout % 10 == 0)
                                            f << std::endl;
                                    }
                            }
                    }
            }
            if (nout % 10 != 0)
                f << std::endl;
            f << "/" << std::endl;
        }
    }

    return 0;
}

int appendVTK(const std::string &vtk_name, bool &vtu, int wvtk, int permt,
              double scalex, double scaley, double scalez,
              int lnx, int rnx, int lny, int rny, int lnz, int rnz,
              int refx, int refy, int refz, int N, int nz, int ny, int nx, int prec,
              std::vector<std::vector<double>> &perm,
              std::vector<std::vector<double>> &permnew)
{
    const int nl[3] = {3, 6, 1};
    int nnz = (int)ceil(rnz / (double)nz);
    int nny = (int)ceil(rny / (double)ny);
    int nnx = (int)ceil(rnx / (double)nx);
    std::ofstream fvtk;
    std::string ext = "vtk";
    if (wvtk == 3 || wvtk == 4)
    {
        ext = "vtu";
    }
    if (wvtk == 1 || wvtk == 3)
        std::cout << "Writing hexahedral mesh." << std::endl;
    else if (wvtk == 2 || wvtk == 4)
        std::cout << "Writing tetrahedral mesh." << std::endl;
    else
    {
        std::cout << "Unknown type of mesh " << wvtk << " (1:hexahedral, 2:tetrahedral, 3:hexahedral(vtu), 4:tetrahedral(vtu)), setting hexahedral." << std::endl;
        wvtk = 1;
    }
    fvtk.open(vtk_name + "." + ext, std::ios::app);

    if (permnew.size() < 1)
    {
        std::cout << "No perm data to write!" << std::endl;
        return -1;
    }
    std::cout << "write PERM to VTK file" << std::endl;
    if (vtu)
    {
        fvtk << "\t\t\t\t<DataArray Name=\"PERM\" NumberOfComponents=\"" << nl[permt] << "\" type=\"Float64\" format=\"ascii\">" << std::endl;
    }
    else
    {
        fvtk << "SCALARS PERM double " << nl[permt] << std::endl;
        fvtk << "LOOKUP_TABLE default" << std::endl;
    }
    for (int k = 0; k < nz * nnz; ++k)
    {
        for (int kr = 0; kr < refz; ++kr)
            for (int j = 0; j < ny * nny; ++j)
            {
                for (int jr = 0; jr < refy; ++jr)
                    for (int i = 0; i < nx * nnx; ++i)
                    {
                        for (int ir = 0; ir < refx; ++ir)
                            if (i >= lnx && i < rnx &&
                                j >= lny && j < rny &&
                                k >= lnz && k < rnz)
                            {
                                int ind = wrap(i, nx) + wrap(j, ny) * nx + wrap(k, nz) * nx * ny;
                                int cells = 1;
                                if (wvtk == 2)
                                    cells = 6;
                                for (int q = 0; q < cells; ++q)
                                {
                                    for (int l = 0; l < nl[permt]; ++l)
                                    {
                                        if (permt == 0)
                                            fvtk << perm[l][ind] << " ";
                                        else if (permt == 1)
                                            fvtk << permnew[l][ind] << " ";
                                        else if (permt == 2)
                                            fvtk << sqrt(pow(perm[0][ind], 2) + pow(perm[1][ind], 2) + pow(perm[2][ind], 2));
                                    }
                                    fvtk << std::endl;
                                }
                            }
                    }
            }
    }
    fvtk << std::endl;
    if (vtu)
        fvtk << "\t\t\t\t</DataArray>" << std::endl;
    std::cout << "done with PERM in VTK file" << std::endl;

    if (vtu)
    {
        ext = "vtu";
        fvtk << "\t\t\t</CellData>" << std::endl;
        fvtk << "\t\t</Piece>" << std::endl;
        fvtk << "\t</UnstructuredGrid>" << std::endl;
        fvtk << "</VTKFile>" << std::endl;
    }
    std::cout << "Closing VTK file " << vtk_name << "." << ext << std::endl;
    fvtk.close();
    return 0;
}

int writeVTK(const std::string &vtk_name, bool &vtu, int wvtk,
             double scalex, double scaley, double scalez,
             int lnx, int rnx, int lny, int rny, int lnz, int rnz,
             int refx, int refy, int refz, int N, int nz, int ny, int nx, int prec,
             std::vector<double> &map, std::vector<double> &poro)
{
    double *map_data = map.data();
    std::ofstream fvtk;
    std::string ext = "vtk";
    if (wvtk == 3 || wvtk == 4)
    {
        ext = "vtu";
        vtu = true;
    }
    std::cout << "Opening " << vtk_name << "." << ext << " for output." << std::endl;
    if (wvtk == 1 || wvtk == 3)
        std::cout << "Writing hexahedral mesh." << std::endl;
    else if (wvtk == 2 || wvtk == 4)
        std::cout << "Writing tetrahedral mesh." << std::endl;
    else
    {
        std::cout << "Unknown type of mesh " << wvtk << " (1:hexahedral, 2:tetrahedral, 3:hexahedral(vtu), 4:tetrahedral(vtu)), setting hexahedral." << std::endl;
        wvtk = 1;
    }
    fvtk.open(vtk_name + "." + ext);
    if (vtu)
    {
        fvtk << "<VTKFile type=\"UnstructuredGrid\" version=\"1.0\">" << std::endl;
        fvtk << "\t<UnstructuredGrid>" << std::endl;
    }
    else
    {
        fvtk << "# vtk DataFile Version 2.0" << std::endl;
        fvtk << "vtk file" << std::endl;
        fvtk << "ASCII" << std::endl;
        fvtk << "DATASET UNSTRUCTURED_GRID" << std::endl;
    }
    if (prec > 0)
        fvtk << std::setprecision(prec);

    std::cout << "write coordinates to VTK file" << std::endl;
    size_t npx = (rnx - lnx) * refx + 1;
    size_t npy = (rny - lny) * refy + 1;
    size_t npz = (rnz - lnz) * refz + 1;
    size_t npoints = npx * npy * npz;
    if (vtu)
    {
        size_t ncx = (rnx - lnx) * refx;
        size_t ncy = (rny - lny) * refy;
        size_t ncz = (rnz - lnz) * refz;
        size_t ncells = ncx * ncy * ncz;
        fvtk << "\t\t<Piece NumberOfPoints=\"" << npoints << "\" NumberOfCells=\"" << ncells << "\">" << std::endl;
    }
    if (vtu)
    {
        fvtk << "\t\t\t<Points>" << std::endl;
        fvtk << "\t\t\t\t<DataArray type=\"Float64\" Name=\"Points\" NumberOfComponents=\"3\" format=\"ascii\">" << std::endl;
    }
    else
        fvtk << "POINTS " << npoints << " double" << std::endl;
    //~ write_points_vtk(lnx,rnx,refx,lny,rnx,refy,lnz,rnz,refz,max,min);
    // double xyz[3], xyzout[3];
    for (int k = lnz; k <= rnz; ++k)
    {
        for (int kr = 0; kr < (k < rnz ? refz : 1); ++kr)
        {
            for (int j = lny; j <= rny; ++j)
            {
                for (int jr = 0; jr < (j < rny ? refy : 1); jr++)
                {
                    for (int i = lnx; i <= rnx; ++i)
                    {
                        for (int ir = 0; ir < (i < rnx ? refx : 1); ir++)
                        {
                            // bottom point
                            xyz[0] = 300.0 * scalex * (i * 1. * refx + ir) / (60.0 * refx);
                            xyz[1] = 300.0 * scaley * (j * 1. * refy + jr) / (60.0 * refy);
                            xyz[2] = 300.0 * scalez * (k * 1. * refz + kr) / (60.0 * refz);
                            transform(map_data, xyz, max, min, ztop, zbottom, nrmtop, nrmbottom, N);
                            changexyz(xyz, max, min, ztop, zbottom, xyzout);
                            fvtk << xyzout[0] << " " << xyzout[1] << " " << xyzout[2] << std::endl;
                        }
                    }
                }
            }
        }
    }
    fvtk << std::endl;
    if (vtu)
    {
        fvtk << "\t\t\t\t</DataArray>" << std::endl;
        fvtk << "\t\t\t</Points>" << std::endl;
    }
    std::cout << "done with coordinates in VTK file" << std::endl;

    std::cout << "write cells to VTK file" << std::endl;
    npx = (rnx - lnx) * refx + 1;
    npy = (rny - lny) * refy + 1;
    npz = (rnz - lnz) * refz + 1;
    std::size_t ncx = (rnx - lnx) * refx;
    std::size_t ncy = (rny - lny) * refy;
    std::size_t ncz = (rnz - lnz) * refz;
    std::size_t ncells = ncx * ncy * ncz;
    std::size_t records = 9 * ncells;
    if (wvtk == 2)
    {
        ncells *= 6;
        records = ncells * 5;
    }
    if (vtu)
    {
        fvtk << "\t\t\t<Cells>" << std::endl;
        fvtk << "\t\t\t\t<DataArray type=\"UInt64\" Name=\"connectivity\" format=\"ascii\">" << std::endl;
    }
    else
        fvtk << "CELLS " << ncells << " " << records << std::endl;
    for (int k = lnz; k < rnz; ++k)
    {
        for (int kr = 0; kr < refz; ++kr)
        {
            for (int j = lny; j < rny; ++j)
            {
                for (int jr = 0; jr < refy; ++jr)
                {
                    for (int i = lnx; i < rnx; ++i)
                    {
                        for (int ir = 0; ir < refx; ++ir)
                        {
                            size_t nvtx[8] =
                                {
                                    (i - lnx) * refx + ir + ((j - lny) * refy + jr) * npx + ((k - lnz) * refz + kr) * npx * npy,
                                    (i - lnx) * refx + ir + 1 + ((j - lny) * refy + jr) * npx + ((k - lnz) * refz + kr) * npx * npy,
                                    (i - lnx) * refx + ir + 1 + ((j - lny) * refy + jr + 1) * npx + ((k - lnz) * refz + kr) * npx * npy,
                                    (i - lnx) * refx + ir + ((j - lny) * refy + jr + 1) * npx + ((k - lnz) * refz + kr) * npx * npy,
                                    (i - lnx) * refx + ir + ((j - lny) * refy + jr) * npx + ((k - lnz) * refz + kr + 1) * npx * npy,
                                    (i - lnx) * refx + ir + 1 + ((j - lny) * refy + jr) * npx + ((k - lnz) * refz + kr + 1) * npx * npy,
                                    (i - lnx) * refx + ir + 1 + ((j - lny) * refy + jr + 1) * npx + ((k - lnz) * refz + kr + 1) * npx * npy,
                                    (i - lnx) * refx + ir + ((j - lny) * refy + jr + 1) * npx + ((k - lnz) * refz + kr + 1) * npx * npy};
                            if (wvtk == 1 || wvtk == 3)
                            {
                                if (!vtu)
                                    fvtk << 8; // for vtu goes to offsets
                                for (int q = 0; q < 8; ++q)
                                    fvtk << " " << nvtx[q];
                                fvtk << std::endl;
                            }
                            else if (wvtk == 2 || wvtk == 4)
                            {
                                int ntet[6][4] =
                                    {
                                        {0, 1, 3, 7},
                                        {0, 1, 7, 5},
                                        {0, 5, 7, 4},
                                        {1, 2, 3, 6},
                                        {1, 6, 3, 7},
                                        {1, 6, 7, 5}};
                                for (int c = 0; c < 6; ++c)
                                {
                                    if (!vtu)
                                        fvtk << 4; // for vtu goes to offsets
                                    for (int q = 0; q < 4; ++q)
                                        fvtk << " " << nvtx[ntet[c][q]];
                                    fvtk << std::endl;
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    fvtk << std::endl;
    if (vtu)
    {
        fvtk << "\t\t\t\t</DataArray>" << std::endl;
        fvtk << "\t\t\t\t<DataArray type=\"UInt64\" Name=\"offsets\" format=\"ascii\">" << std::endl;
        size_t offset = 0;
        for (int k = lnz; k < rnz; ++k)
        {
            for (int kr = 0; kr < refz; ++kr)
            {
                for (int j = lny; j < rny; ++j)
                {
                    for (int jr = 0; jr < refy; ++jr)
                    {
                        for (int i = lnx; i < rnx; ++i)
                        {
                            for (int ir = 0; ir < refx; ++ir)
                            {
                                if (wvtk == 1 || wvtk == 3)
                                {
                                    offset += 8;
                                    fvtk << offset;
                                    fvtk << std::endl;
                                }
                                else if (wvtk == 2 || wvtk == 4)
                                {
                                    for (int c = 0; c < 6; ++c)
                                    {
                                        offset += 4;
                                        fvtk << offset;
                                    }
                                    fvtk << std::endl;
                                }
                            }
                        }
                    }
                }
            }
        }
        fvtk << "\t\t\t\t</DataArray>" << std::endl;
        fvtk << "\t\t\t\t<DataArray type=\"UInt8\" Name=\"types\" format=\"ascii\">" << std::endl;
    }
    else
        fvtk << "CELL_TYPES " << ncells << std::endl;
    for (int k = lnz; k < rnz; ++k)
    {
        for (int kr = 0; kr < refz; ++kr)
        {
            for (int j = lny; j < rny; ++j)
            {
                for (int jr = 0; jr < refy; ++jr)
                {
                    for (int i = lnx; i < rnx; ++i)
                    {
                        for (int ir = 0; ir < refx; ++ir)
                        {
                            int cells = 1;
                            int ctype = 12;
                            if (wvtk == 2 || wvtk == 4)
                            {
                                cells = 6;
                                ctype = 10;
                            }
                            for (int q = 0; q < cells; ++q)
                                fvtk << ctype << std::endl;
                        }
                    }
                }
            }
        }
    }
    fvtk << std::endl;
    if (vtu)
    {
        fvtk << "\t\t\t\t</DataArray>" << std::endl;
        fvtk << "\t\t\t</Cells>" << std::endl;
    }
    std::cout << "done with cells in VTK file" << std::endl;

    std::cout << "Writing properties data." << std::endl;

    if (wvtk && !vtu)
    {
        size_t ncx = (rnx - lnx) * refx;
        size_t ncy = (rny - lny) * refy;
        size_t ncz = (rnz - lnz) * refz;
        size_t ncells = ncx * ncy * ncz;
        if (wvtk == 2)
            ncells *= 6;
        fvtk << "CELL_DATA " << ncells << std::endl;
    }

    if (wvtk && vtu)
        fvtk << "\t\t\t<CellData>" << std::endl;

    int nnz = (int)ceil(rnz / (double)nz);
    int nny = (int)ceil(rny / (double)ny);
    int nnx = (int)ceil(rnx / (double)nx);

    std::cout << "write PORO to VTK file" << std::endl;
    if (vtu)
    {
        fvtk << "\t\t\t\t<DataArray Name=\"PORO\" NumberOfComponents=\"1\" type=\"Float64\" format=\"ascii\">" << std::endl;
    }
    else
    {
        fvtk << "SCALARS PORO double" << std::endl;
        fvtk << "LOOKUP_TABLE default" << std::endl;
    }
    for (int k = 0; k < nz * nnz; ++k)
    {
        for (int kr = 0; kr < refz; ++kr)
            for (int j = 0; j < ny * nny; ++j)
            {
                for (int jr = 0; jr < refy; ++jr)
                    for (int i = 0; i < nx * nnx; ++i)
                    {
                        for (int ir = 0; ir < refx; ++ir)
                            if (i >= lnx && i < rnx &&
                                j >= lny && j < rny &&
                                k >= lnz && k < rnz)
                            {
                                int ind = wrap(i, nx) + wrap(j, ny) * nx + wrap(k, nz) * nx * ny;
                                int cells = 1;
                                if (wvtk == 2)
                                    cells = 6;
                                for (int q = 0; q < cells; ++q)
                                    fvtk << poro[ind] << std::endl;
                            }
                    }
            }
    }
    fvtk << std::endl;
    if (vtu)
        fvtk << "\t\t\t\t</DataArray>" << std::endl;
    std::cout << "done with PORO in VTK file" << std::endl;

    return 0;
}

bool readWellData(const std::string &well_file, std::map<double, std::vector<double>> &well_data, std::vector<std::string> &properties)
{
    std::ifstream fin(well_file);
    if (!fin)
    {
        std::cerr << "Error: 无法打开井数据文件 " << well_file << std::endl;
        return false;
    }

    std::string line;
    int pro_size = 0;
    while (std::getline(fin, line))
    {
        if (line.empty())
        {
            continue; // 跳过空行和注释行
        }
        if (line.size() > 8 && line.substr(0, 9) == "CURVENAME")
        {
            if (line.find("=") != std::string::npos)
            {
                std::size_t pos = line.find("=");
                std::string prop_name = line.substr(pos + 1);
                pos = prop_name.find_first_of(",");
                while (pos != std::string::npos)
                {
                    std::string v = prop_name.substr(0, pos);
                    auto p1 = v.find_first_not_of(" ");
                    auto p2 = v.find_last_not_of(" ");

                    properties.push_back(v.substr(p1, p2));
                    prop_name = prop_name.substr(pos + 1);
                    pos = prop_name.find_first_of(",");
                    pro_size++;
                }
                {
                    std::string v = prop_name.substr(0, pos);
                    auto p1 = v.find_first_not_of(" ");
                    auto p2 = v.find_last_not_of(" ");

                    properties.push_back(v.substr(p1, p2));
                    prop_name = prop_name.substr(pos + 1);
                    pos = prop_name.find_first_of(",");
                    pro_size++;
                }
            }
        }

        if (line.size() > 5 && line.substr(0, 6) == "#DEPTH")
        {
            // std::getline(fin, line); // 跳过标题行
            while (std::getline(fin, line))
            {
                std::vector<double> data_row(pro_size + 1);
                std::istringstream iss(line);
                double value = 0.0f;
                for (int i = 0; i < pro_size + 1; ++i)
                {
                    if (iss >> value)
                    {
                        data_row[i] = value; // 如果读取失败，设置为0
                    }
                }
                well_data.insert({data_row[0], data_row});
            }
            break;
        }
    }
    return true;
}
int main(int argc, char *argv[])
{
    system("chcp 65001 > nul");
    if (argc < 2)
    {
        help(argv[0]);
        return 1;
    }

    auto opts = parseCommandLine(argc, argv);
    if (opts.size() < 1)
    {
        return 2;
    }

    bool pass = checkCommands(opts);
    if (!pass)
    {
        return 3;
    }

    std::string output = std::string(parseValue(opts, "output", ""));
    std::string mapfile = std::string(parseValue(opts, "mapfile", ""));
    std::string horizons_file = std::string(parseValue(opts, "horizons", ""));
    std::string well_files = std::string(parseValue(opts, "well", ""));

    double scalex = parseValue(opts, "scalex", 1.0);
    double scaley = parseValue(opts, "scaley", 1.0);
    double scalez = parseValue(opts, "scalez", 1.0);
    double deformation = parseValue(opts, "deformation", 0.5);
    int rnx = parseValue(opts, "rnx", 60);
    int rny = parseValue(opts, "rny", 60);
    int rnz = parseValue(opts, "rnz", 60);

    int lnx = parseValue(opts, "lnx", 0);
    int lny = parseValue(opts, "lny", 0);
    int lnz = parseValue(opts, "lnz", 0);

    int refx = parseValue(opts, "refx", 1);
    int refy = parseValue(opts, "refy", 1);
    int refz = parseValue(opts, "refz", 1);

    int wvtk = parseValue(opts, "wtk", 1);
    if (opts.count("wvtk"))
        wvtk = parseValue(opts, "wvtk", wvtk);

    double xmin = parseValue(opts, "xmin", 0.0);
    double xmax = parseValue(opts, "xmax", 300.0);
    double ymin = parseValue(opts, "ymin", 0.0);
    double ymax = parseValue(opts, "ymax", 300.0);
    double zmin = parseValue(opts, "zmin", 0.0);
    double zmax = parseValue(opts, "zmax", 300.0);

    bool wecl = parseValue(opts, "ecl", true);
    int permt = parseValue(opts, "permt", 0);
    int prec = parseValue(opts, "prec", 0);

    // rnx = 110, rny = 110, rnz = 100;
    // xmin = 19178749.0, xmax = 19186699.0;
    // ymin = 3366759.0, ymax = 3374709.0;
    // zmin =400, zmax = 2400;

    printf("lnx=%d, rnx=%d, lny=%d, rny=%d, lnz=%d, rnz=%d\n", lnx, rnx, lny, rny, lnz, rnz);
    printf("refx=%d, refy=%d, refz=%d\n", refx, refy, refz);
    printf("xmin=%.2f, xmax=%.2f, ymin=%.2f, ymax=%.2f, zmin=%.2f, zmax=%.2f\n", xmin, xmax, ymin, ymax, zmin, zmax);
    printf("scalex=%.2f, scaley=%.2f, scalez=%.2f\n", scalex, scaley, scalez);
    printf("deformation=%.2f\n", deformation);
    printf("permt=%d, prec=%d\n", permt, prec);
    printf("wvtk=%d\n", wvtk);
    printf("wecl=%d\n", wecl);
    if (rnx < lnx || rny < lny || rnz < lnz)
    {
        std::cout << "Error: 区间设置错误！请检查 lnx, rnx, lny, rny, lnz, rnz 的值。" << std::endl;
        return 4;
    }

    int N = 128;
    auto map_data = createMapMat(mapfile, N, deformation);
    std::string outMapFile = "processed_map_new.txt";
    std::ofstream mout(outMapFile);
    if (!mout)
    {
        std::cerr << "Error: 无法打开输出文件 " << outMapFile << std::endl;
        return -1;
    }

    for (int row = 0; row < N; ++row)
    {
        for (int col = 0; col < N; ++col)
        {
            mout << map_data[row * N + col];
            if (col < N - 1)
                mout << ' ';
        }
        mout << '\n';
    }
    mout.close();
    std::cout << "已导出归一化后的 map 到 " << outMapFile << std::endl;

    int nx = rnx-lnx, ny = rny-lny, nz = rnz-lnz;
    auto horizon_data = readHorizonData(horizons_file, nz);
    // auto poro = ReadProData("spe_phi.dat", nz, ny, nx);
    std::vector<double> poro;

    std::map<double, std::vector<double>> well_data;
    std::vector<std::string> properties;
    bool succ = readWellData(well_files, well_data, properties);
    if (!succ)
    {
        std::cout << " Error happens when reading file " << well_files << std::endl;
    }
    std::size_t nout = 0;
    if (wecl)
    {
        std::cout << "Writing ECL file." << std::endl;
        writeECL(output, prec,
                 scalex, scaley, scalez,
                 lnx, rnx, lny, rny, lnz, rnz,
                 refx, refy, refz, N, nz, ny, nx, xmin, xmax, ymin, ymax, zmin, zmax,
                 map_data, nout, poro, well_data, properties);
    }
    bool vtu = false;
    if (wvtk)
    {
        std::cout << "Writing VTK file." << std::endl;
        writeVTK(output, vtu, wvtk,
                 scalex, scaley, scalez,
                 lnx, rnx, lny, rny, lnz, rnz,
                 refx, refy, refz, N, nz, ny, nx,
                 prec, map_data, poro);
    }

    std::vector<std::vector<double>> perm;
    std::vector<std::vector<double>> permnew;
    // ReadPermData("spe_perm.dat", nz, ny, nx, perm, permnew, permt, scalex, scaley, scalez,
    //              map_data, N);

    appendECL(output, prec, permt,
              scalex, scaley, scalez,
              lnx, rnx, lny, rny, lnz, rnz,
              nx, ny, nz,
              refx, refy, refz,
              perm, permnew);
    if (wvtk)
    {
        appendVTK(output, vtu, wvtk, permt,
                  scalex, scaley, scalez,
                  lnx, rnx, lny, rny, lnz, rnz,
                  refx, refy, refz, N, nz, ny, nx, prec,
                  perm, permnew);
    }

    return 0;
}