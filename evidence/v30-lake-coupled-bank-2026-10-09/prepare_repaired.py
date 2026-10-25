from pathlib import Path
B=Path(__file__).parent
extra='''
def crossing_lower_bound(h,p,f):
 # Wet endpoint is immutable. Solve t=dw/(dw+hd-Fd) <= t_before+4.1/edge_length.
 # Both the physical plane P and the frozen visible field F are consumed.
 lower=np.full(h.shape,-np.inf);rr,cc=np.nonzero(np.isfinite(p));n=h.shape[1]
 ids=np.stack((rr*n+cc,rr*n+cc+1,(rr+1)*n+cc,(rr+1)*n+cc+1),axis=1)
 ground=h.ravel()[ids];edges=[(0,1,6.),(0,2,6.),(0,3,6*2**.5),(1,3,6.),(2,3,6.)]
 for field in (np.repeat(p[rr,cc,None],4,axis=1),f[rr,cc]):
  d=field-ground
  for a,b,length in edges:
   for wet,dry in ((a,b),(b,a)):
    choose=(d[:,wet]>0)&(d[:,dry]<0)
    dw=d[choose,wet];dd=d[choose,dry];old=dw/(dw-dd);maximum=np.minimum(1.,old+4.1/length)
    limit=field[choose,dry]+dw*(1/maximum-1)+1e-6
    # Inactive limits beyond the edge don't restrict existing source heights.
    np.maximum.at(lower.ravel(),ids[choose,dry],np.minimum(ground[choose,dry],limit))
 return lower

'''
s=(B/'author.py').read_text();s=s.replace("assert not (B/'authoring.json').exists(),'one coupled-bank candidate'","assert not (B/'authoring-repaired.json').exists(),'one implementation repair: enforce existing crossing constraint'")
s=s.replace("np.savez_compressed(B/'constraints.npz'", "minimum=np.maximum(minimum,crossing_lower_bound(original,p,f))\n np.savez_compressed(B/'constraints-repaired.npz'")
s=s.replace("target=B/'candidate'","target=B/'candidate-repaired'").replace("B/'terrain-delta.npz'","B/'terrain-delta-repaired.npz'").replace("sha(B/'constraints.npz')","sha(B/'constraints-repaired.npz')").replace("(B/'authoring.json').write_text","(B/'authoring-repaired.json').write_text")
s=s.replace("if __name__=='__main__':main()",extra+"if __name__=='__main__':main()")
(B/'author_repaired.py').write_text(s)
s=(B/'verify.py').read_text().replace("B/'candidate/terrain.npz'","B/'candidate-repaired/terrain.npz'").replace("B/'verification.json'","B/'verification-repaired.json'")
(B/'verify_repaired.py').write_text(s)
(B/'implementation-repair.md').write_text('''# Reparación única de implementación

El candidato original conserva física y reduce forma35,5%/32,9%, pero desplaza un cruce5,8593m. La regla4,1m estaba en el plan y el consumidor, faltaba en el autor. Se resuelve analíticamente el límite inferior del extremo seco de cada arista cruzada por P/F. El extremo mojado es fijo. No se cambian objetivo, pesos, radio, presupuesto ni umbrales. Se retiene candidato/reporte original y se escribe candidate-repaired separado. Si falla, no otra variante.
''',encoding='utf-8')
print('Prepared one constraint implementation repair, original candidate preserved.')
