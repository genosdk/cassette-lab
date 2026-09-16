#include "Engine.h"
#include <array>
#include <cstdlib>
#include <iostream>
void check(bool ok) { if (!ok) { std::cerr << "Engine test failed\n"; std::exit(1); } }
int main() {
    for (double rate : {44100., 48000., 96000., 192000.}) {
        cassette::Engine a, b;
        a.prepare(rate, 0, 0, 1); b.prepare(rate, 0, 0, 1);
        std::array<float, 5000> x{}, y{};
        x.fill(0.25f); y.fill(-0.5f);
        float* stereo[] = {x.data(), y.data()};
        a.process(stereo, 2, 0); a.process(stereo, 2, 5000);
        for (int n=0;n<5000;++n) check(x[n]==0.25f && y[n]==-0.5f);
        x.fill(1); y.fill(1);
        a.setParameters(6, -3, 0.5f); b.setParameters(6, -3, 0.5f);
        float* one[] = {x.data()}; a.process(one, 1, 5000);
        for (int n=0;n<5000;) {
            int count=std::min(37,5000-n); float* ptr[]={y.data()+n};
            b.setParameters(6,-3,0.5f); b.process(ptr,1,count); n+=count;
        }
        for (int n=0;n<5000;++n) check(std::isfinite(x[n]) && std::abs(x[n]-y[n])<1e-6f);
        float expected=(0.5f+0.5f*std::pow(10.f,6.f/20.f))*std::pow(10.f,-3.f/20.f);
        check(std::abs(x.back()-expected)<1e-5f);
    }
    std::cout << "Unity, channel isolation, zero block, smoothing and block invariance passed\n";
}
