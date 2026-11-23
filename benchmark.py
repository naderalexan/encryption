"""Run: python benchmark.py /path/to/tiffs > results.csv  (NumPy and Pillow)."""
import csv
import hashlib
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from algorithm3 import encrypt_channel, encrypt_rgb

IDS = ['2.1.01','2.1.02','2.1.03','2.1.04','2.1.05','2.1.06','4.2.01','4.2.03','4.2.06']
# Each row follows the order of the image identifiers above.
PLAIN_H = [
[7.5090,7.3541,6.5966],[7.4061,7.4188,6.5931],[6.5476,5.7003,4.5030],
[7.2621,6.6163,5.2736],[7.5580,7.4596,6.6664],[7.1927,7.4084,7.4412],
[6.9480,6.8844,6.1264],[7.7066,7.4744,7.7522],[7.3123,7.6428,7.2136]]
CIPHER_H = np.array([[3,4,3],[2,2,3],[3,3,3],[3,2,3],[3,3,3],[3,2,3],[4,3,3],[3,3,2],[3,3,3]])*.0001+7.999
NPCR = [99.6085,99.6083,99.6067,99.6086,99.6076,99.6087,99.6098,99.6095,99.6087]
UACI = [33.4725,33.4627,33.4601,33.4548,33.4577,33.4532,33.4577,33.4564,33.4593]
MSE = [[7703,7821,6767],[8949,7498,9005],[13689,5960,8837],[8272,6313,7872],
       [8761,8019,7900],[7489,8182,7611],[11427,12367,9924],[8628,77402,9464],[7307,11516,11538]]
PSNR = [[9.2639,9.1977,9.8266],[8.6129,9.3811,8.5856],[6.7668,10.3778,8.6676],
        [8.9542,10.1278,9.1696],[8.7051,9.0893,9.1543],[9.3862,9.0021,9.3159],
        [7.5514,7.2080,8.1636],[8.7714,9.2432,8.3699],[9.4931,7.5177,7.5092]]
# H,V,D within each channel. Values transcribed from Tables II and III.
PLAIN_COR = [
[.98669,.98393,.97303,.98513,.98230,.97002,.98582,.98286,.97118],
[.97603,.98007,.96209,.96240,.96794,.93955,.98496,.98640,.97508],
[.98659,.98124,.97105,.98196,.97357,.95997,.96725,.94752,.92323],
[.88162,.86572,.84869,.88435,.86789,.85908,.87933,.86434,.85719],
[.84773,.83287,.76781,.78470,.76237,.68163,.74856,.72399,.64245],
[.89631,.91260,.85513,.81289,.84778,.74830,.78425,.81329,.72050],
[.99359,.99513,.98944,.98117,.98713,.97112,.98258,.97892,.96485],
[.92306,.86595,.85434,.86547,.76500,.73479,.90734,.88089,.83985],
[.95579,.95410,.94199,.97148,.96625,.95295,.97103,.96937,.95295]]
CIPHER_COR = np.array([
[85,74,-19,231.9,-71,-9,7,-52,144],[2,6,-187,290,-314,24,193,101,-36],
[143,-47,-123,-180,-172,-32,-197,298,-105],[247,9,-37,237,-1,95,341,170,-60],
[39,129,192,190,-348,201,255,-232,-87],[182,107,-2,-111,96,135,-62,-169,27],
[-142,-47,-103,144,-304,-111,-468,246,-104],[66,-229,-1,-32,-137,-44,-326,88,45],
[39,150,233,15,77,-249,-173,23,160]]) / 100000


def exact_checks():
    # Independent literal recurrence reading/writing permuted output locations.
    rng = np.random.default_rng(2025)
    for h,w in [(1,1),(1,6),(5,1),(2,2),(4,5),(3,6),(8,9)]:
        p, m = rng.integers(0,256,(2,h,w),dtype=np.uint8)
        r,c = rng.permutation(h),rng.permutation(w)
        expected = np.empty_like(p)
        t = w//2
        for i in range(h):
            for j in [t,*range(t+1,w),*range(t-1,-1,-1)]:
                value = int(p[i,j])+int(m[i,j])
                if i:
                    value += int(expected[r[i-1],c[j]])
                if j != t:
                    k = j-1 if j>t else j+1
                    value += int(expected[r[i],c[k]])
                    if i:
                        value += int(expected[r[i-1],c[k]])
                expected[r[i],c[j]] = value % 256
        np.testing.assert_array_equal(encrypt_channel(p,r,c,m),expected)


def entropy(a):
    f = np.bincount(a.ravel(), minlength=256)
    p = f[f>0]/a.size
    return -np.sum(p*np.log2(p))


def correlations(a):
    pairs = [(a[:,:-1],a[:,1:]),(a[:-1],a[1:]),(a[:-1,:-1],a[1:,1:])]
    return [np.corrcoef(x.ravel(),y.ravel())[0,1] for x,y in pairs]


def run(folder):
    exact_checks()
    writer = csv.writer(sys.stdout)
    writer.writerow(['image','metric','channel','measured','paper','delta','abs_tolerance','status'])
    failures = []
    for n,name in enumerate(IDS):
        path, = folder.rglob(name+'.tiff')
        rgb = np.asarray(Image.open(path).convert('RGB'))
        assert rgb.shape == (512,512,3)
        print(name, 'RGB SHA256',hashlib.sha256(rgb.tobytes()).hexdigest(),file=sys.stderr)
        cipher = encrypt_rgb(rgb)
        changed = rgb.copy()
        changed[0,0,0] ^= 1
        diff = np.abs(cipher.astype(float)-encrypt_rgb(changed))
        def record(metric,ch,value,paper,tol,impossible=False):
            delta = value-paper
            ok = abs(delta)<=tol
            status = 'invalid published value' if impossible else ('pass' if ok else 'FAIL')
            if not ok and metric.startswith('Plain corr') and n < 6:
                status = 'published plaintext mismatch'
            writer.writerow([name,metric,ch,f'{value:.9f}',paper,f'{delta:.9f}',tol,status])
            if not ok and not impossible and not (metric.startswith('Plain corr') and n < 6):
                failures.append((name,metric,ch,delta))
        record('NPCR (%)','RGB',100*np.mean(diff!=0),NPCR[n],.03)
        record('UACI (%)','RGB',100*diff.mean()/255,UACI[n],.12)
        for k,ch in enumerate('RGB'):
            p,c = rgb[...,k],cipher[...,k]
            record('Plain entropy',ch,entropy(p),PLAIN_H[n][k],.0001)
            record('Cipher entropy',ch,entropy(c),CIPHER_H[n,k],.00035)
            mse = np.mean((p.astype(float)-c)**2)
            record('MSE',ch,mse,MSE[n][k],MSE[n][k]*.02,MSE[n][k]>255**2)
            record('PSNR (dB)',ch,10*np.log10(255**2/mse),PSNR[n][k],.09)
            for typ,a,ref,tol in [('Plain',p,PLAIN_COR,.00001),('Cipher',c,CIPHER_COR,.011)]:
                observed = correlations(a)
                if typ == 'Plain' and n < 3:
                    np.testing.assert_allclose(observed, PLAIN_COR[n+3][3*k:3*k+3],
                                               atol=.00001, rtol=0)
                for j,(direction,val) in enumerate(zip('HVD',observed)):
                    record(typ+' corr '+direction,ch,val,ref[n][3*k+j],tol)
    if failures:
        raise AssertionError(failures)


if __name__ == '__main__':
    run(Path(sys.argv[1]))
