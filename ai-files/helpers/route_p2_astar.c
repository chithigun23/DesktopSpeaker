// route_p2_astar.c : multi-layer 8-direction A* on a raster. gcc -O2 -shared -fPIC -o route_p2_astar.so route_p2_astar.c -lm
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdint.h>
typedef struct { float f; int32_t s; } HN;
static HN *heap; static int64_t hn, hcap;
static void hpush(float f, int32_t s){ if(hn>=hcap){hcap*=2; heap=realloc(heap,hcap*sizeof(HN));}
  int64_t i=hn++; while(i>0){int64_t p=(i-1)/2; if(heap[p].f<=f)break; heap[i]=heap[p]; i=p;} heap[i].f=f; heap[i].s=s; }
static HN hpop(void){ HN top=heap[0]; HN l=heap[--hn]; int64_t i=0; for(;;){int64_t c=2*i+1; if(c>=hn)break; if(c+1<hn&&heap[c+1].f<heap[c].f)c++; if(heap[c].f>=l.f)break; heap[i]=heap[c]; i=c;} heap[i]=l; return top; }
static const int DX[8]={1,1,0,-1,-1,-1,0,1}, DY[8]={0,1,1,1,0,-1,-1,-1};
// code: nl*H*W uint8 (0 blocked, 1..4 allowed class). src/tgt: nl*H*W uint8. viaok: H*W uint8. lay_ok: nl uint8
// stepcost[5]: cost per cell step for code 1..4. out path: int32 triples (layer,y,x), returns count or -1
int astar(int nl,int H,int W,const uint8_t*code,const uint8_t*src,const uint8_t*tgt,const uint8_t*viaok,const uint8_t*lay_ok,
          const uint8_t*pen,const float*stepcost,float viacost,float turnpen,float hw,int ty,int tx,int32_t*path,int maxpath,int64_t maxexp){
  int64_t NC=(int64_t)nl*H*W; int64_t NS=NC*8;
  float*g=malloc(NS*sizeof(float)); int32_t*par=malloc(NS*sizeof(int32_t)); uint8_t*cl=calloc(NS,1);
  if(!g||!par||!cl) return -2;
  for(int64_t i=0;i<NS;i++) g[i]=1e30f;
  hcap=1<<20; heap=malloc(hcap*sizeof(HN)); hn=0;
  // state = cell*8+dir ; dir 8 = none -> use dir index 0 for starts with par=-1 and cost 0 (turn penalty ignored)
  for(int l=0;l<nl;l++) for(int y=0;y<H;y++) for(int x=0;x<W;x++){ int64_t c=((int64_t)l*H+y)*W+x; if(src[c]&&lay_ok[l]){ for(int d=0;d<8;d++){ int64_t s=c*8+d; g[s]=0; par[s]=-1; float h=hw*hypotf(y-ty,x-tx); hpush(h,(int32_t)s);} } }
  int64_t exp=0; int64_t found=-1;
  while(hn>0){ HN n=hpop(); int64_t s=n.s; if(cl[s])continue; cl[s]=1; int64_t c=s/8; int d=s%8; float gs=g[s];
    if(tgt[c]){found=s;break;}
    if(++exp>maxexp)break;
    int l=c/((int64_t)H*W); int r=c%((int64_t)H*W); int y=r/W,x=r%W;
    for(int nd=0;nd<8;nd++){ int ny=y+DY[nd],nx=x+DX[nd]; if(ny<0||ny>=H||nx<0||nx>=W)continue; int64_t nc=((int64_t)l*H+ny)*W+nx; uint8_t cd=code[nc]; if(!cd&&!tgt[nc])continue; if(!cd) cd=4;
      if(nd&1){ // diagonal: both orthogonal neighbours must be non-blocked
        if(!code[((int64_t)l*H+y)*W+nx]||!code[((int64_t)l*H+ny)*W+x])continue; }
      float step=stepcost[cd]*((nd&1)?1.41421356f:1.0f)+pen[nc];
      int dd=abs(nd-d); if(dd>4)dd=8-dd; float tp=(c==-1||gs==0)?0:turnpen*dd; // turn penalty
      float ng=gs+step+tp; int64_t ns=nc*8+nd; if(ng<g[ns]){g[ns]=ng;par[ns]=(int32_t)s; hpush(ng+hw*hypotf(ny-ty,nx-tx),(int32_t)ns);} }
    if(viaok[r]){ for(int nl2=0;nl2<nl;nl2++){ if(nl2==l||!lay_ok[nl2])continue; int64_t nc=((int64_t)nl2*H)*W+r; if(!code[nc]&&!tgt[nc])continue; // via lands on allowed cell
        if(code[nc]&&code[nc]>2) continue; // via only on wide-ish cells
        float ng=gs+viacost; int64_t ns=nc*8+d; if(ng<g[ns]){g[ns]=ng;par[ns]=(int32_t)s;hpush(ng+hw*hypotf(y-ty,x-tx),(int32_t)ns);} } }
  }
  int cnt=-1;
  if(found>=0){ cnt=0; int64_t s=found; while(s>=0&&cnt<maxpath){ int64_t c=s/8; int l=c/((int64_t)H*W); int r=c%((int64_t)H*W); path[cnt*3]=l;path[cnt*3+1]=r/W;path[cnt*3+2]=r%W;cnt++; s=par[s]; } }
  free(g);free(par);free(cl);free(heap);
  return cnt;
}
