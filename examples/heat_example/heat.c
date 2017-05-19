
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/timeb.h>
#include <zmq.h>
#ifdef BUILD_WITH_MPI
#include <mpi.h>
#endif // BUILD_WITH_MPI
#include <melissa_api.h>

void read_file(int*   ,
               int*   ,
               double*,
               double*,
               double*);

void load(int*,
          int*,
          int*,
          int*,
          int* );

void init(double*,
          int*   ,
          int*   ,
          double*,
          double*,
          int*   ,
          double*,
          double*,
          double* );

void filling_A(double*,
               double*,
               double*,
               double*,
               int*   ,
               int*   ,
               double* );

void filling_F(int*   ,
               int*   ,
               double*,
               double*,
               double*,
               double*,
               double*,
               double*,
               double*,
               int*   ,
               int*   ,
               double*,
               double*,
               double* );

void conjgrad(double*,
              double*,
              double*,
              int*   ,
              int*   ,
              double*,
              int*   ,
              int*   ,
              int*   ,
              int*   ,
              int*   ,
              int*   ,
              int*    );

void finalize(double*,
              double*,
              int*   ,
              int*   ,
              int*   ,
              int*   ,
              double*,
              double*,
              int*   ,
              int*    );

int main( int argc, char **argv )
{

  int    nx, ny, n, nmax, me, np, i1, in, nb_op, next, previous;
  double lx, ly, dt, dx, dy, d, t, epsilon, t1, t2, temp;
  double *u = NULL;
  double *f = NULL;
  double a[3];
  double param[5];
  int sobol_rank = 0;
  int sobol_group = 0;
  MPI_Comm comm;
  int coupling = 1;
  int fcomm;
  char *field_name = "heat";
  struct timeb tp;

  MPI_Init(&argc, &argv);

  if (argc < 2)
  {
      fprintf (stderr, "Missing parameter");
      return -1;
  }

  for (n=0; n<5; n++)
      param[n] = 0;
    if (argc > n+1)
    {
       param[n] = strtod(argv[n+1], NULL);
    }
  temp = param[0];
  if (argc > 3)
  {
    sobol_rank  = (int)strtol(argv[argc-2], NULL, 10);
  }
  if (argc > 2)
  {
    sobol_group = (int)strtol(argv[argc-1], NULL, 10);
  }

  MPI_Comm_split(MPI_COMM_WORLD, sobol_rank, me, &comm);
  MPI_Comm_rank(comm, &me);
  MPI_Comm_size(comm, &np);
  fcomm = MPI_Comm_c2f(comm);


  ftime(&tp);
  t1 = (double)tp.time + (double)tp.millitm / 1000;

  next = me+1;
  previous = me-1;

  if(next == np)     next=MPI_PROC_NULL;
  if(previous == -1) previous=MPI_PROC_NULL;

  read_file(&nx, &ny, &lx, &ly, &d);

  n = nx*ny;
  load(&me, &n, &np, &i1, &in);

  nb_op   = in-i1+1;
  dt      = 0.01;
  nmax    = 100;
  dx      = lx/(nx+1);
  dy      = ly/(ny+1);
  epsilon = 0.0001;

  u = malloc(nb_op * sizeof(double));
  f = malloc(nb_op * sizeof(double));
  init(&u[0], &i1, &in, &dx, &dy, &nx, &lx, &ly, &temp);
  filling_A (&d, &dx, &dy, &dt, &nx, &ny, &a[0]); /* fill A */

  melissa_init (&nb_op, &np, &me, &sobol_rank, &sobol_group, &comm, &coupling);

  for(n=1; n<=nmax; n++)
  {
    t+=dt;
    filling_F (&nx, &ny, &u[0], &d, &dx, &dy, &dt, &t, &f[0], &i1, &in, &lx, &ly, &param[0]);
    conjgrad (&a[0], &f[0], &u[0], &nx, &ny, &epsilon, &i1, &in, &np, &me, &next, &previous, &fcomm);
  }

  n = 1;
  melissa_send (&n, field_name, u, &me, &sobol_rank, &sobol_group);
  finalize (&dx, &dy, &nx, &ny, &i1, &in, &u[0], &f[0], &me, &sobol_group);

  melissa_finalize ();

  ftime(&tp);
  t2 = (double)tp.time + (double)tp.millitm / 1000;

  fprintf(stdout, "Calcul time: %g sec\n", t2-t1);
  fprintf(stdout, "Final time step: %g\n", t);

  MPI_Finalize();

  return 0;
}
