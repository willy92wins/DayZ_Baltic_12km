"""Compare every decoded LOD field, allowing only physical offsets and Roadway face order."""
import json,struct
def normalized(x):
    if isinstance(x,float):return {'float64_bits':struct.pack('<d',x).hex()}
    if x is None or isinstance(x,(str,int,bool)):return x
    if isinstance(x,bytes):return {'bytes_hex':x.hex()}
    if isinstance(x,(list,tuple)):return [normalized(v) for v in x]
    if isinstance(x,dict):return {str(k):normalized(v) for k,v in x.items()}
    if hasattr(x,'__dict__'):
        return {k:normalized(v) for k,v in vars(x).items() if k not in ('declared_end','parsed_end')}
    if hasattr(x,'__slots__'):
        return {k:normalized(getattr(x,k)) for k in x.__slots__ if hasattr(x,k)}
    raise TypeError(type(x))
def canonical_lod(lod):
    value=normalized(lod)
    if abs(lod.resolution-3e15)/3e15>=1e-4:return value
    # No face/section-referencing structures are silently discarded. The
    # present static Roadway has neither selections nor proxies; reject others.
    if lod.named_selections or lod.proxies:
        raise ValueError('Roadway with selections/proxies needs an explicit remap')
    labelled=[];assigned=[]
    for section in lod.sections:
        t=section.texture_index;m=section.material_index
        if not(-1<=t<len(lod.textures) and -1<=m<len(lod.materials)):
            raise ValueError('Invalid section index')
        attrs=normalized(section)
        for key in ('face_lower','face_upper','texture_index','material_index'):attrs.pop(key)
        attrs['resolved_texture']=None if t==-1 else lod.textures[t]
        attrs['resolved_material']=None if m==-1 else normalized(lod.materials[m])
        indices=section.get_face_indices(lod.faces)
        if not indices:raise ValueError('Empty Roadway section')
        for index in indices:
            ids=tuple(lod.faces[index].vertex_indices)
            if len(ids)!=3 or len(set(ids))!=3 or min(ids)<0 or max(ids)>=len(lod.vertices):
                raise ValueError('Valid indexed triangle required')
            cycle=min(ids,ids[1:]+ids[:1],ids[2:]+ids[:2])
            labelled.append(json.dumps(dict(vertices=cycle,section=attrs),sort_keys=True))
        assigned.extend(indices)
    if sorted(assigned)!=list(range(len(lod.faces))):
        raise ValueError('Every face must belong to exactly one section')
    value.pop('faces');value.pop('sections');value['labelled_faces']=sorted(labelled)
    return value

